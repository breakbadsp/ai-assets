---
name: FiveCsOfRequirement
description: "Solidify requirements before design. Check that they are complete, correct, concise, clear, and concrete."
disable-model-invocation: true
---

# FiveCsOfRequirement

Before design, review and refine the requirement or bug report. Do not design or build in this step.

## Checks

- Complete: the goal, the scope (in and out), the users or callers, and the edge cases that change the result are stated. A bug report also has the steps to reproduce, expected and actual behavior, version or commit, environment, and evidence (log, error, screenshot).
- Correct: the statement agrees with the code, the docs, and the evidence. The named files, functions, flags, and versions exist. A bug report describes a defect, not intended behavior.
- Concise: one problem per requirement. No solution is prescribed unless it is a constraint. No duplicate or unrelated items.
- Clear: each term has one meaning. Each sentence has one reading. No "fast", "better", "handle", or "etc." without a measure.
- Concrete: each acceptance criterion is a test that passes or fails, with inputs, outputs, and numbers.

## Method

1. Read the request, linked issues, and only the code needed to check Correct.
2. Fix what the evidence or an obvious answer settles. Record each fix that changes meaning as an assumption, and tell the user.
3. Ask the user only about a gap where two plausible answers give different behavior and no evidence decides. Ask all such questions at one time, each with a recommended answer.
4. Keep the result in proportion: a few lines for a small task.

## Output

```markdown
## Requirement
Problem: <one or two sentences>
Scope: in <...>; out <...>
Bug only: steps <...>; expected <...>; actual <...>; environment <...>
Acceptance criteria:
- [ ] <test that passes or fails>
Assumptions: <each meaning change, or "none">
```
