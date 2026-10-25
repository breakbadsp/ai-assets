---
description: LoomFlow - build a task or review a PR - size first, then build, two reviewers, one fixer, one gate. Max two review rounds, then hand over to the user.
argument-hint: [supervised] <task> | <PR number>
---

Run LoomFlow for $ARGUMENTS. You are the orchestrator.

If the repository has `docs/loomflow.md`, follow it and the repository's `.claude/commands/loomflow.md` and `.claude/agents/`, not this file. Otherwise follow this file.

## Modes

- First argument is a PR number or URL: review mode. Start at "Review mode". Do not review or edit code yourself.
- Otherwise: build mode, with the arguments as the task. Build, open the PR, then run review mode in the same run.
- Autopilot is the default. A leading `supervised`, or a user request before the task starts, selects supervised mode: the user approves the plan or design note, and the start of the merge gate.

## Sizes and models

Decide the size first, before any work. In doubt, use the larger size. Pass the model and effort to every role.

| Size | When | Builder | Reviewer A | Reviewer B | Analyzer |
| --- | --- | --- | --- | --- | --- |
| Small | at most 30 lines in at most 3 files, or documentation only, and no sensitive path | orchestrator | Sonnet 5.5, medium | Haiku 5.5, medium | Sonnet 5.5, medium |
| Normal | most changes | orchestrator | GPT 6.1 Sol or Sonnet 5.5, medium | Haiku 5.5, medium | Sonnet 5.5, medium |
| Major | a new feature or redesign; any change on a sensitive path; concurrency, storage, wire format, auth, or secrets; or more than 300 changed code lines | Opus 5.5, high; orchestrator when Major only for path or area | GPT 6.1 Sol, high (Opus 5.5, high, when Sol is unavailable) | Sonnet 5.5, high | Sonnet 5.5, high |

The default merge gate model is Haiku 5.5, `low`. Use two model families for A and B when possible. Lower the effort, never the size, when the budget is low.

- By default, do not use Astra 6 or effort above `high`. Only the following exceptions apply.
- When the Claude usage limit is reached, continue on Codex. Opus 5.5 `high` becomes GPT 6.1 Sol `xhigh`; Sonnet 5.5 becomes GPT 6.1 Sol at the same effort; Haiku becomes GPT 6.1 Sol `low`. Use Astra 6 `medium` only when required for this fallback.
- UI/UX design review uses Astra 6 `medium`. This role does not require a different model family or an increase to `high`. It gives no Astra exception for code review or build.
- Non-UI Major design review: use the Major Reviewer A model, of a family other than the builder's at `high` when available. Apply the usage-limit fallback above when needed.

## Build mode

1. State the size and the reason in one line. Create a worktree and branch (never the primary checkout or `master`).
2. Small, Normal, and Major only for path or area: build, run the repository check, push, and open the PR (Normal: a plan of 3 to 5 lines in the PR body). Go to "Review mode" (Major review for a Major change).
3. Major build (a new feature or redesign, or more than 300 changed code lines): stay thin. Do no file reads or edits yourself. Start one `general-purpose` builder with the builder model. It opens a draft PR whose body is the minimal design note (requirement; x over y and why; what is deleted; the one fact that makes it safe). It never merges, starts agents, or runs `/loomflow`.
4. One design reviewer uses the model and effort selected above and posts `## Design review, round <n>`. Over-design is a finding. The builder revises once. Run round 2 only when a design `blocker` is not `FIXED`. Never run a third.
5. Continue the same builder: build, prove (tests, short DOM facts; screenshots only for a major UI redesign), write the safety fact and its proof in the PR body, and mark the PR ready. Go to "Review mode" with the Major size.

## Review mode

1. `gh pr view <PR> --json number,state,headRefName,headRefOid,url`. Stop if the PR is closed or merged. Use the worktree that holds the PR branch. `git fetch origin`. HEAD must equal `headRefOid`, and `git status --porcelain` must print nothing. Otherwise stop and report.
2. Start `pr-adversarial-reviewer` twice in parallel: Reviewer A (ID prefix `A`, lens: correctness, concurrency, memory safety, failure paths) and Reviewer B (ID prefix `B`, lens: requirements, tests, `AGENTS.md` rules, docs accuracy). Pass the PR number, worktree path, prefix, lens, round number, and head SHA. Reviewers also check the safety fact and proof that the PR body states. They run nothing.
3. Confirm that both reviews start with `## Reviewer A, round <n>, head <SHA>` and `## Reviewer B, round <n>, head <SHA>`. If either is missing, stop and report. After each read-only role, HEAD and the worktree must be unchanged.
4. With a `blocker` or `major` finding, start `pr-comment-analyzer` with pass type `review` and the round number. Check that its `## Analyzer, round <n>` comment gives an outcome for each such ID and that each `FIXED` commit is in the PR head.
5. If round 1 changed the head, run round 2 on `git diff <round-1 head>..<head>` and the `FIXED` outcomes only. After round 2, an open `blocker` or `major` (not `FIXED` or `REBUTTED`) stops the run for manual handling.

## Merge gate (once)

Start `pr-test-merger` with the gate model and effort selected above, the PR number, worktree path, expected head SHA, and run number 1. Read its `## Merge gate, run 1, head <SHA>` comment. If it failed, do not retry and do not start a fix pass. Report the failing gates.

## Limits

- At most two review rounds and one gate run. A run never starts `/loomflow` again, and its agents never run it.
- Pass each agent the model and effort selected above, including its usage-limit and UI/UX design-review exceptions.
- Never merge with an open `blocker` or `major` issue (also a user-raised `critical`) or a failing check. Never use `--admin` or force.
- If a result is ambiguous, stop and report.
- On every exit, also a stop, append one tab-separated row to `${XDG_STATE_HOME:-$HOME/.local/state}/loomflow/<owner>-<repo>.tsv` (a new file starts with the header row): `date`, `mode`, `size`, `task_or_pr`, `rounds`, `blockers`, `majors`, `gate`, `outcome`, `models`, `peak_context`, `lesson`. Write `-` for an unknown value.

## Final report (under 10 lines)

PR URL, size, design rounds, review rounds, findings per severity per round, outcomes, gate result, and the merge SHA or the open issues. Mark commits pushed after the last review as not reviewed.
