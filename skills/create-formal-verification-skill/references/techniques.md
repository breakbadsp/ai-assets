# Choose a verification technique

Use the cheapest technique that covers the risk in all cases that matter. Start at the top of the first table, and go down only when the risk needs it.

## Techniques, cheapest first

| # | Technique | What it proves | Example tools | Cost |
| --- | --- | --- | --- | --- |
| 1 | Types | Classes of error cannot occur: null, wrong unit, illegal state. | C++ strong types and `enum class`, Rust ownership, TypeScript strict, `mypy --strict` | Very low |
| 2 | Static analysis | No undefined behavior, leak, or race on the analyzed paths. | `clang-tidy`, Clang Static Analyzer, Infer, CodeQL, Frama-C EVA | Low |
| 3 | Assertions and contracts | Preconditions, postconditions, and invariants hold on each run. | `assert`, `static_assert`, C++26 contracts, `debug_assert!` | Low |
| 4 | Exhaustive table test | Each state and event pair of a small finite system is correct. | The repository test framework | Low |
| 5 | Property-based test | A property holds for generated inputs; failures shrink to a minimal case. | RapidCheck, Hypothesis, fast-check, proptest | Low to medium |
| 6 | Fuzzing with sanitizers | No crash or sanitizer error on mutated inputs. | libFuzzer, AFL++, `cargo fuzz`; ASan, UBSan, TSan | Low to medium |
| 7 | Mutation testing | The tests detect a change in the code. It checks the tests. | Mull, Stryker, mutmut, cargo-mutants | Medium |
| 8 | Model-based stateful test | The code matches a simple reference model over random operation sequences. | RapidCheck state, Hypothesis `RuleBasedStateMachine`, fast-check `commands` | Medium |
| 9 | Concurrency testing | No race or deadlock in the explored interleavings. | TSan, Loom, Coyote, Jepsen-style fault injection | Medium |
| 10 | Design model checking | Every order of events in the model is safe, and the system makes progress, within bounds. | TLA+ with TLC or Apalache, P, Alloy | Medium to high |
| 11 | Bounded model checking of code | No assertion failure or undefined behavior for every input up to a bound. | CBMC, ESBMC, Kani | Medium |
| 12 | Symbolic execution | Inputs that reach a bug, found by path exploration. | KLEE, Crucible | Medium to high |
| 13 | Deductive verification | The code meets its contracts for every input, with no bound. | Dafny, Frama-C WP, SPARK, Verus, Prusti | High |
| 14 | Interactive proof | A full proof of a deep property. | Lean, Rocq, Isabelle | Very high |
| 15 | Trace validation | The real code behaves like the verified model. | Model-generated tests, TLA+ trace validation | Medium |
| 16 | Differential or equivalence test | A new version gives the same output as the old one or a reference. | Same inputs into two implementations, CBMC equivalence | Low to medium |
| 17 | Structure lint | No module cycle; each type keeps its fields, so one boundary owns each invariant. | `deslop-please` (Rust), `import-linter` (Python), `dependency-cruiser` (TypeScript), include-graph checks (C++) | Low |

## Technique by change or component

| Change or component | Main risk | First choice | Add when a mistake is costly |
| --- | --- | --- | --- |
| Domain types, IDs, units, money | Mix-ups, illegal states | 1 | 3 |
| Pure function, calculation, data transform | Wrong edge cases | 5 | 13 on the core |
| Parser, decoder, wire or file format | Crash or memory bug on bad input | 6 | 5 round trip (`decode(encode(x)) == x`), 11 |
| Small state machine, one actor | A missed transition | 4 | 10 only when more actors appear |
| Stateful component: cache, store, queue API | Wrong result after a call sequence | 8 | 10 for invalidation |
| Concurrency: locks, atomics, lock-free code | Race, deadlock, lost update | 9 | 10 for the design, 11 on the code |
| Distributed protocol: retries, leases, sagas | Bad order of events, partial failure | 10 before code | 15, 9 with fault injection |
| Crash and restart, migration, storage format | Data loss, broken upgrade | 10 for recovery steps, 16 old against new | 6 on the format |
| Hot path, low-latency C++ | Undefined behavior, overflow, an optimization breaks an invariant | 3, 2, 16 against a simple reference | 11 on core functions |
| Refactor with no behavior change | Silent behavior change | 16 | 7 |
| New module or type, or a change to module boundaries | Leaked fields, cycles, an invariant with no single owner | 17 | 3 at the owning boundary |
| Auth and permissions | Access that must be denied | 4 over roles and actions | 13 for the policy |
| Unsafe or low-level code | Memory safety | 6 with ASan | 11, 13 |
| Algorithm with a deep correctness claim | Wrong in rare cases | 5 | 10 or 14 |
| UI layout, docs, configuration, one-off script | Visible and cheap to fix | Existing tests or a verification journey | None |

A model (10) checks the design, not the code. Link it to the code: turn each counterexample into a test, put each invariant in the code as 3 or 5, and run the model in CI when its covered code changes.

## Value against cost

Keep a check only when its value is greater than its cost. Ask for each new or existing check:

- Value: which defect does it catch, how likely is that defect, and what does the defect cost? Would another check already catch it?
- Cost: time to write, run time in CI, flakiness, and the edits that it forces on each future change.
- Can it fail? A check that passes on a broken variant has no value.

Decide one of: create, update, keep, or remove. Remove a check that duplicates a stronger one, tests implementation details, or is flaky with no fix. Record each decision and its reason in one line.
