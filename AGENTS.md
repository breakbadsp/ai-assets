# Global guidance

Use [ASD-STE100 Simplified Technical English](https://www.asd-ste100.org/)
for all written communication. Use short, active sentences and consistent
technical names. Avoid idioms and contractions. Preserve exact identifiers,
commands, paths, and quoted text. Consult the specification when needed.

## Keep work lean

- Keep replies brief. Use plain text by default. Create visualizations,
  reports, or other artifacts only when requested or necessary for the task.
- Read only applicable instructions and needed file sections. Reuse verified
  results. Limit tool output to the information needed for the next decision.
- Keep optional skills, plugins, and MCP servers disabled by default.
  Enable them only when the user requests a task that needs them.
- Run required checks. Avoid repeated checks and extra deliverables without
  a clear need. Keep durable rules short and maintain one source per rule.
- Write docs only for what code cannot show: why x was chosen over y,
  constraints, and how to operate or verify. Do not restate code in docs.
- Give mechanical work (merge gates, data gathering, mechanical edits, tests
  from a clear specification) to Haiku. By default, do not use Astra 6 or
  reasoning effort above high. Only the following exceptions apply.
- When the Claude usage limit is reached, continue on Codex. Opus 5.5 high
  becomes GPT 6.1 Sol xhigh; Sonnet 5.5 becomes GPT 6.1 Sol at the same
  effort; Haiku becomes GPT 6.1 Sol low. Use Astra 6 medium only when
  required for this fallback.
- Use Astra 6 medium for UI/UX design review. This role does not require a
  different model family or an increase to high. It gives no Astra exception
  for code review or build.

## C++

Before writing, editing, or reviewing C++ code, read the `cpp-principles`
skill. The C++ rules are one skill per topic, in
`$HOME/ai/skills/cpp-*/SKILL.md`. Read only the skill for the step in hand:

- `cpp-naming-and-layout`: naming anything, braces, indentation.
- `cpp-references-pointers-const`: a parameter or local variable: value, reference, or pointer; `const` or not.
- `cpp-functions`: a function's design, return values, parameter count.
- `cpp-error-handling`: a function that can fail; `throw`, `try`, `catch`, `noexcept`.
- `cpp-assertions`: invariants, preconditions, `static_assert`.
- `cpp-classes-and-composition`: a class or struct, special members, inheritance, `const` member functions.
- `cpp-resource-management`: ownership, RAII, smart pointers, C handles.
- `cpp-expressions-and-statements`: initialization, `constexpr` values, casts, narrowing, integer arithmetic.
- `cpp-concurrency`: threads, locks, atomics, shared data.
- `cpp-templates`: templates, concepts, type aliases.
- `cpp-standard-library`: containers, text types, formatting, new dependencies.
- `cpp-hot-path`: code that runs for each event at a high rate, performance changes.
- `cpp-source-files`: headers, includes, namespaces.
- `cpp-comments`: comments and test descriptions.
- `cpp-checklist`: before C++ work is done, and in C++ review.

## Shared skills

These skills apply to every project. Each is in `$HOME/ai/skills/<name>/SKILL.md`.
They are manual-only. Read the matching `SKILL.md` when its situation occurs,
and follow it. At the start of non-trivial work, name the skills that apply
and read them. Read them again at the step they govern: tests, blast radius
before a shared change, proof before done. Give their names to subagents that
do the work.

- `principle-laziness-protocol`: refactoring, judging diff size, or tempted to add abstractions.
- `principle-subtract-before-you-add`: sequencing an addition, refactor, or rewrite.
- `principle-build-the-lever`: any non-trivial edit, migration, or analysis.
- `principle-prove-it-works`: before declaring a task done.
- `principle-fix-root-causes`: debugging.
- `principle-attack-the-premise`: two or more fixes sharing one premise have failed.
- `principle-boundary-discipline`: validation, error handling, framework adapters.
- `principle-encode-lessons-in-structure`: the same instruction or correction recurs.
- `principle-minimize-reader-load`: code that is hard to trace.
- `principle-model-the-domain`: stateful logic or heavy branching.
- `principle-migrate-callers-then-delete-legacy-apis`: a new internal API while old callers remain.
- `principle-test-behavior-not-implementation`: writing or changing tests.
- `principle-guard-the-context-window`: context filling up with large outputs or repeated reads.
- `principle-sequence-verifiable-units`: multi-step work, sweeps, and stacked commits or PRs.
- `principle-type-system-discipline`: designing types or signatures in statically typed code.
- `principle-foundational-thinking`: choosing core types and data structures before logic.
- `principle-redesign-from-first-principles`: a new requirement meets an existing design.
- `blast-radius`: finding what a change could break elsewhere before it ships.
- `create-verification-skill`: building a project-local end-to-end verification skill.
- `unslop`: cutting AI-style wording from prose you write.
- `typescript-best-practices`: reading or editing TypeScript and TSX.
- `architect`: substantial design or redesign before implementation.
- `visual-parity`: preserving an existing interface during migration.
