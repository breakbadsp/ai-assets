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

## C++

Before writing, editing, or reviewing C++ code, read and apply
`$HOME/ai/conventions/cpp.md`. It applies only to C++.

## Shared skills

These skills apply to every project. Each is in `$HOME/ai/skills/<name>/SKILL.md`.
They are manual-only. Read the matching `SKILL.md` when its situation occurs,
and follow it.

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
