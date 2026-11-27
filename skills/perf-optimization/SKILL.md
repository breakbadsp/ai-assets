---
name: perf-optimization
description: "The performance improvement plan: set a goal, build tests that measure it, profile in all ways, write a bottleneck report, remove unnecessary work first, then fix memory, I/O, CPU, and data layout in that order, and prove each change. Read at the start of any performance work; it sends each step to its perf-* skill."
disable-model-invocation: true
---

# Performance improvement plan

Performance work is a loop: measure, find the largest cost, remove or reduce
it, measure again. Most wasted effort comes from optimizing a part that is not
the bottleneck, or from a result that was noise. The steps below prevent both.

## The steps

| Step | Do this | Skill | Gate to the next step |
| --- | --- | --- | --- |
| 0. Goal | Write the metric, the scenario, and the target. | This skill | The goal is a number. |
| 1. Tests | Build the workload and the benchmarks that measure the goal. | `perf-benchmarks` | The benchmark is repeatable and drives the code under test. |
| 2. Profile | Profile the scenario in all ways: CPU, memory, I/O, waits, cache. | `perf-profiling` | You know which resource saturates first. |
| 3. Report | Write the bottleneck report. | This skill | Each bottleneck has a cost and a cause. |
| 4. Remove work | For each bottleneck: is the work needed at all? | `perf-remove-work` | Nothing unnecessary is left on the hot path. |
| 5. Memory | Allocations, copies, page faults. | `perf-memory` | No allocation in the steady state. |
| 6. I/O | Avoid, batch, or reduce system calls and device work. | `perf-io` | Each system call carries a batch. |
| 7. CPU | Reduce, batch, vectorize, or parallelize the necessary work. | `perf-cpu` | The CPU work matches the algorithm's need. |
| 8. Data layout | Fix cache misses with data-oriented design. | `perf-data-oriented-design` | The hot loops read contiguous, used bytes. |
| 9. Prove and guard | A/B proof, then a regression test. | `perf-profiling` section 9, `perf-benchmarks` | The gain is above the noise and a test keeps it. |

Steps 5 to 8 are a default order, not a rule. Go first to the resource that
the report shows as the bottleneck. The order exists because removing work
(step 4) often removes the allocations, I/O, and CPU work too, and an
allocation or a system call is often cheaper to remove than CPU work.

After each change, go back to step 2. The bottleneck moves. Stop when the goal
is met: more speed past the goal costs code clarity for no gain.

## Step 0: write the goal

Write one line: the metric, the scenario, and the target. Examples:

- "p99 order latency below 50 µs at 200k orders/s, 4 clients."
- "Engine cost below 100 ns per command with the market feed on."
- "Import 10 GB in less than 2 minutes on one core."

Without a number, you cannot know when to stop, and you cannot reject a change
that makes the code harder to read for a gain that nobody needs.

## Step 3: write the bottleneck report

Write the report before you change code. Use this form:

```text
Goal:      <metric, scenario, target>; now <current value>
Setup:     <commit, build flags, CPU model, cores and pinning, workload>
Saturated: <the resource that limits the goal, with evidence>
           (for example: "4 clients use 286% of 3 cores; gateway 72% busy")

| # | Bottleneck | Evidence (tool, number) | Cost to the goal | Cause | Next skill |
| 1 | Publish copies 40 levels per command | bench: 206 vs 102 ns/cmd | 50% of engine time | per-event work that a 20 ms reader samples | perf-remove-work |
| 2 | ... |

Not bottlenecks: <costs that you measured and decided to leave, with the reason>
```

Rules for the report:

- **Name what saturates first.** A thread at 100% CPU, a full queue, a disk at
  100% use, or a load generator at its core limit. If the test harness
  saturates first, the test cannot measure the code. Fix the test
  (`perf-benchmarks`) before you change the code.
- **Give each bottleneck its cost to the goal.** A function at 10% of the
  samples of an idle, spinning thread costs nothing. Divide by the busy time,
  not the wall time.
- **Write down what is not a bottleneck.** This stops the next person from
  measuring it again. Example: "No false sharing: all HITM lines are queue
  indexes (true sharing)."

## Rules for every change

- One change at a time, with a measurement before and after.
- Keep a change only if the gain is above the run-to-run spread and moves the
  goal metric.
- A faster change that makes the code harder to read must earn its place
  with a measured gain on the goal. Otherwise, revert it.
- Add a regression test or benchmark for each kept change
  (`perf-benchmarks`).
- Write the result where the project keeps performance notes: the numbers,
  the setup, and the reason.

## Related skills

- `cpp-hot-path`: the C++ rules for code that runs for each event.
- `principle-subtract-before-you-add`: step 4 in general form.
- `principle-prove-it-works`: step 9 in general form.
