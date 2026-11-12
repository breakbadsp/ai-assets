---
name: no-parts-is-best-parts
description: Apply during LoomFlow design, coding, and review when adding a product feature or component. Require a clear need and benefit before adding complexity.
disable-model-invocation: true
---

# No parts is Best parts

Inspired by Elon's principle that the best part is no part.

Add a feature or component only when it is necessary for the agreed requirement
and makes the product better. Each addition must justify its cost to users,
operation, and maintenance.

## Design

- State the user problem and the result that must improve.
- First check whether the current product can meet the requirement. Consider
  removing, simplifying, or changing an existing part before adding one.
- For each proposed addition, ask what fails without it. If the requirement
  still holds, omit the addition. Defer parts needed only for possible future use.
- Choose the smallest design that meets the requirement. State why any new
  component is necessary and how to verify its benefit in the existing plan.

## Coding

- Apply the same check to new controls, settings, dependencies, services,
  abstractions, and stored state. Use an existing part when it fits the need.
- Remove redundant parts made obsolete by the change within the task scope.
- Preserve required behavior, safety, accessibility, and reliability. Fewer parts
  do not justify shifting necessary work to users or operators.

## Review

- Check each addition against the agreed requirement and its claimed benefit.
- Ask whether omission or a simpler existing part gives the same result.
- Raise a finding when an unnecessary part has a concrete cost or failure risk.
  State the part, the impact, and the simpler option. Use LoomFlow's existing
  severity rules. Do not block a change on a preference for fewer parts alone.
- If the need or benefit is uncertain, state what evidence is missing. Do not
  present an assumption as proof or silently discard an agreed requirement.
