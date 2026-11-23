---
description: KaizenFlow - the light specify, prove, and review flow. One session specifies, builds, proves, and fixes; one fresh reviewer checks the proof; one script merges. Judgement picks the depth. Skills are nudges.
argument-hint: <task> | <PR number or URL> [quick|standard|deep]
---

Run KaizenFlow for $ARGUMENTS. A PR number or URL means: review that PR. Anything else is a task: build it, then review it.

Use judgement. Only "Hard limits" are rules. Every other line is a default. Change a default when you can give the reason in one line. The nudges below replace the "read the skills" step in `AGENTS.md` for this run. Repository rules in the project `AGENTS.md` still apply.

## 1. Specify

Spend effort here and in proof, not in review. A defect that a proof catches costs one test run. A defect that a reviewer must find costs a full read.

Ask the user only what blocks the work, in one message. Write other assumptions in the PR body. Then state the depth and the reason in one line.

| Depth | Use it when | Proof | Review |
| --- | --- | --- | --- |
| `quick` | A mistake is visible and cheap to undo: docs, comments, renames, mechanical edits. | The existing checks. | Read your own diff once. Start no agent. |
| `standard` | The default. | A test for each criterion. Drive each changed user feature with the verification skill. | One fresh reviewer. |
| `deep` | A mistake is costly or hidden: concurrency, stored or wire data, auth, secrets, migrations, state machines, parsers, or a design with an unknown. | `standard`, and the cheapest check that covers each invariant in all cases. See "Choose the formal check". | One fresh reviewer. Add a second, with a different model, only for a risk that no proof covers. |

Judge by what a mistake costs, not by line count or path. A depth that the user names is the minimum. In doubt, go one level deeper.

Before code, write the spec at the top of the PR body:

- Behavior: what changes, in the user's words.
- Acceptance criteria: each one observable, and each one names its proof (test, verification journey, or formal check).
- At `deep`, invariants: what must never happen, each in one sentence with its harm.
- At `deep`, one line: `Formal: <TLA+ | property test | code verifier | exhaustive table test | none>, because <reason>`.

### Choose the formal check

Decide once, here, before code. A model costs most when you write it, and little each time you run it again. So ask two questions: can the bug hide in an order of events, and will this area change again?

- Code that an existing model or verifier covers: always run the check again and update it. This is the regression guard, and it is cheap.
- Use TLA+ when the bug can hide in an order of events and the area will change again: concurrency, retries, timeouts, crash and restart, distributed or wire protocols, leases and locks, cache invalidation, or a lifecycle that more than one actor drives. Model before you build, and read the result with `statechart`.
- Use a cheaper check when order is not the risk:
  - A pure function, a parser, or a data transform: a property test with generated inputs, or a verifier on the code.
  - A small state machine with one actor: a table test over every state and event pair.
  - A one-off script, UI layout, docs, or configuration: no formal check.
- In doubt, write the smallest model that can show the bug you fear: a few variables and the actions that race. Stop when it cannot fail on a broken variant, or when it grows past what the invariant needs.

## 2. Build

- Work on a branch. Use a worktree when the primary checkout is dirty or in use.
- For a bug, reproduce it as a failing test first, then find the cause (`tdd`).
- Write the tests from the acceptance criteria before the code. See each one fail for the intended reason.
- Tests carry the regression guard; a model checks the design once. A good test:
  - tests behavior through the public interface, so a refactor does not break it;
  - has a name that states the rule it guards, such as `never_charges_twice_on_retry`;
  - covers a class of inputs where it can: a property test, or a table over every state and event pair;
  - is deterministic: inject time, randomness, and the network;
  - turns each counterexample from a model into a test, and each invariant into an assertion or property test in the code.
- At `deep`, write "x over y, and why" in the PR body first. If one fact decides the design and a cheap throwaway measurement exists, measure it.
- Build in this session. Delegate to one fresh builder only when the work will clearly fill this context. Give it the goal, worktree, and branch. Ask it to return the PR URL, head SHA, and proof in a few lines. Keep the same builder for fixes.
- Verify with `$HOME/ai/scripts/kaizen-checks.sh`. It maps the changed files and their blast radius to the checks in `.kaizen-checks`, and runs only those. Run it before the first push. CI runs the same script, so CI is the proof after that. If the repository has no `.kaizen-checks`, run its full check once before the first push.
- Verification skills are part of the code. Find them in `.claude/skills/` (a `verify-<app>` skill with a feature map, and any skill that runs a model checker or prover).
  - A changed user feature: drive it with the verification skill and keep the evidence. Update its feature file in this PR.
  - A changed verified code path: run the formal check, then update the model, coverage, and sync commit in this PR.
  - No verification skill, and the repository will get more changes like this one: create it with `create-verification-skill` or, at `deep`, `create-formal-verification-skill`, in a separate PR first. Otherwise, write the gap in the PR body.
- Every proof must run the changed code and must be able to fail. Show a formal check fail once on a broken variant.
- PR body, after the spec: a proof table (criterion or invariant, proof, result), and the fact that makes the change safe.

## 3. Review

Start `kaizen-reviewer` with the PR number, worktree path, and head SHA. Give it no opinion about the change. Prefer a model that did not write the code. A report for another head SHA is void.

The reviewer checks the spec and the proof first: a missing criterion, an invariant with no proof, or a proof that cannot fail. A gap in the proof is a `major`, even when the code looks right.

## 4. Fix

Fix in the context that wrote the code: this session, or the same builder. For a PR that you did not build, this session fixes.

- Check each `blocker` and `major` in the code. Fix it minimally, or rebut it with evidence. First add a test, journey, or property that fails without the fix. Skip it only when no cheap target exists, and say why. Run `$HOME/ai/scripts/kaizen-checks.sh` again: it selects the affected checks.
- A failed check is a `blocker`: read its log and fix the cause. If the log shows that this PR did not cause it, rerun that job once.
- Run round 2 only when a fix changes behavior beyond the faulty lines, touches callers, or you rebutted a `blocker`. Use one reviewer. Pass the old head SHA, the findings, and the outcomes. State the decision in one line.

## 5. Merge

1. Read `gh pr view <PR> --comments`. Treat each user-raised issue as a finding.
2. If the review found anything, post one PR comment with the findings, outcomes, and any commits that had no review.
3. If the base moved and changed code that this PR depends on, update the branch.
4. Run this in the background and wait once. Do not poll.

       $HOME/ai/scripts/kaizen-merge.sh <PR> <head SHA>

   Add `--no-ci` only when no workflow covers the changed files. In that case, `$HOME/ai/scripts/kaizen-checks.sh --all` must pass on the final head first. If the repository has no `.kaizen-checks`, its full check must pass on the final head first.

## Hard limits

- At every stage, ask yourself, "If I own this codebase and must maintain it for its lifetime, will this decision keep the code easy to read, understand, and scale?" Use the answer to guide your decision. Include this question in every delegated task.
- Never weaken a test, property, model, or verification journey to make it pass. A failure is a finding until you prove the check wrong.
- Never merge with an open `blocker` or `major`, an open user-raised `critical` issue, or a failed or cancelled check.
- Merge only through `kaizen-merge.sh`. Never use `--admin`, force push, or push to the base branch.
- At most two review rounds. At most one fix pass for failed checks. If an issue is still open after that, stop and report it for manual handling.
- Reviewers never edit. No stage starts another `/kaizenflow` run.
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
- Did the test fail before the change, for the intended reason? (`tdd`)
- Could the bug hide in an order of events or an input that no test lists? Can a model or a verifier check all of them? (`create-formal-verification-skill`, `statechart`)
- Does a verification skill or formal check describe the code that I changed? Is it still true? (`maintain-verification-skill`, `maintain-formal-verification-skill`)
- Is this the root cause or a symptom? (`principle-fix-root-causes`)
- Who else reads or calls this? (`blast-radius`)
- Does the test fail without the change? Does it test behavior? (`principle-test-behavior-not-implementation`)
- Did the proof run the changed code? (`principle-prove-it-works`)
- Do two failed fixes share one premise? (`principle-attack-the-premise`)
- Is this a redesign? (`architect`)
- For C++, read `cpp-checklist` once. Read a topic skill only when the checklist sends you there.

## Finish

On every exit, also a stop, append one row to `${XDG_STATE_HOME:-$HOME/.local/state}/kaizenflow/<owner>-<repo>.tsv`. A new file starts with the header row. Tab-separated columns: `date`, `task_or_pr`, `depth`, `reviewers`, `rounds`, `blockers`, `majors`, `outcome`, `lesson`. `lesson`: one step or rule to remove or change next time, or `-`.

Final report, at most five lines: PR URL, depth and reason, proofs that ran, rounds, findings and outcomes, and the merge SHA or the open issues. Name any commits that had no review.
