---
description: KaizenFlow - the light build and review flow. One session builds and fixes, one fresh reviewer checks, one script merges. Judgement picks the depth. Skills are nudges.
argument-hint: <task> | <PR number or URL> [quick|standard|deep]
---

Run KaizenFlow for $ARGUMENTS. A PR number or URL means: review that PR. Anything else is a task: build it, then review it.

Use judgement. Only "Hard limits" are rules. Every other line is a default. Change a default when you can give the reason in one line. The nudges below replace the "read the skills" step in `AGENTS.md` for this run. Repository rules in the project `AGENTS.md` still apply.

## 1. Frame

Ask the user only what blocks the work, in one message. Write other assumptions in the PR body. Then state the depth and the reason in one line.

| Depth | Use it when | Review |
| --- | --- | --- |
| `quick` | A mistake is visible and cheap to undo: docs, comments, renames, mechanical edits. | Read your own diff once. Start no agent. |
| `standard` | The default. | One fresh reviewer. |
| `deep` | A mistake is costly or hidden: concurrency, stored or wire data, auth, secrets, migrations, or a design with an unknown. | Two fresh reviewers in parallel, with different models. |

Judge by what a mistake costs, not by line count or path. A depth that the user names is the minimum. In doubt, go one level deeper.

## 2. Build

- Work on a branch. Use a worktree when the primary checkout is dirty or in use.
- For a bug, reproduce it and find the cause first.
- At `deep`, write "x over y, and why" in the PR body first. If one fact decides the design and a cheap throwaway measurement exists, measure it.
- Build in this session. Delegate to one fresh builder only when the work will clearly fill this context. Give it the goal, worktree, and branch. Ask it to return the PR URL, head SHA, and proof in a few lines. Keep the same builder for fixes.
- Verify with `scripts/kaizen-checks.sh`. It maps the changed files and their blast radius to the checks in `.kaizen-checks`, and runs only those. Run it before the first push. CI runs the same script, so CI is the proof after that. If the repository has no `.kaizen-checks`, run its full check once before the first push.
- PR body, in a few lines: the goal, the acceptance criteria, and the fact that makes the change safe with its proof.

## 3. Review

Start `kaizen-reviewer` with the PR number, worktree path, and head SHA. Give it no opinion about the change. Prefer a model that did not write the code. A report for another head SHA is void.

## 4. Fix

Fix in the context that wrote the code: this session, or the same builder. For a PR that you did not build, this session fixes.

- Check each `blocker` and `major` in the code. Fix it minimally, or rebut it with evidence. Add a test that fails without the fix when a cheap target exists. Run `scripts/kaizen-checks.sh` again: it selects the affected checks.
- A failed check is a `blocker`: read its log and fix the cause. If the log shows that this PR did not cause it, rerun that job once.
- Run round 2 only when a fix changes behavior beyond the faulty lines, touches callers, or you rebutted a `blocker`. Use one reviewer. Pass the old head SHA, the findings, and the outcomes. State the decision in one line.

## 5. Merge

1. Read `gh pr view <PR> --comments`. Treat each user-raised issue as a finding.
2. If the review found anything, post one PR comment with the findings, outcomes, and any commits that had no review.
3. If the base moved and changed code that this PR depends on, update the branch.
4. Run this in the background and wait once. Do not poll.

       $HOME/ai/scripts/kaizen-merge.sh <PR> <head SHA>

   Add `--no-ci` only when no workflow covers the changed files. In that case, `scripts/kaizen-checks.sh --all` must pass on the final head first.

## Hard limits

- Never merge with an open `blocker` or `major`, an open user-raised `critical` issue, or a failed or cancelled check.
- Merge only through `kaizen-merge.sh`. Never use `--admin`, force push, or push to the base branch.
- At most two review rounds. At most one fix pass for failed checks. If an issue is still open after that, stop and report it for manual handling.
- Reviewers never edit. Nothing in this flow starts `/kaizenflow` or `/loomflow`.
- If a result is ambiguous, stop and report.

## Context budget

Each call reads the full context again, so the cost of this session is calls times context size.

- Make fewer calls. Batch independent commands. Do not read a file again.
- Find with `grep`, then read only the function. Limit output with `tail`, `--quiet`, or `--json`.
- Keep screenshots and browser snapshots out of this context. Let a subagent get UI proof and return short facts.
- Do not repeat a report. Pass it on or act on it.

## Nudges

Ask the question. Read the skill in `$HOME/ai/skills/` only when the question does not settle the matter.

- Does this need to exist? Would the requirement still hold without it? (`no-parts-is-best-parts`)
- What can I delete first? What is the smallest diff? (`principle-subtract-before-you-add`, `principle-laziness-protocol`)
- Is the requirement testable? Which gap changes the result? (`FiveCsReview`)
- Is this the root cause or a symptom? (`principle-fix-root-causes`)
- Who else reads or calls this? (`blast-radius`)
- Does the test fail without the change? Does it test behavior? (`principle-test-behavior-not-implementation`)
- Did the proof run the changed code? (`principle-prove-it-works`)
- Do two failed fixes share one premise? (`principle-attack-the-premise`)
- Is this a redesign? (`architect`)
- For C++, read `cpp-checklist` once. Read a topic skill only when the checklist sends you there.

## Finish

On every exit, also a stop, append one row to `${XDG_STATE_HOME:-$HOME/.local/state}/kaizenflow/<owner>-<repo>.tsv`. A new file starts with the header row. Tab-separated columns: `date`, `task_or_pr`, `depth`, `reviewers`, `rounds`, `blockers`, `majors`, `outcome`, `lesson`. `lesson`: one step or rule to remove or change next time, or `-`.

Final report, at most five lines: PR URL, depth and reason, rounds, findings and outcomes, and the merge SHA or the open issues. Name any commits that had no review.
