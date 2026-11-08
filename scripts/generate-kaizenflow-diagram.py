#!/usr/bin/env python3
"""Generate the detailed KaizenFlow view. Use --check to detect a stale SVG.

Operating sources: claude/commands/kaizenflow.md,
claude/agents/kaizen-reviewer.md, and scripts/kaizen-merge.sh.
"""
import argparse
from html import escape
from pathlib import Path
import textwrap
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'docs/kaizenflow.svg'
WIDTH = 1600
CARD_WIDTH = 344
COLS = (82, 452, 822)

# Cards in each band describe a stage. They are not separate agent handoffs.
STAGES = [
    ('FRAME', 'Choose the depth by the cost of a mistake.', [
        ('entry', 'TASK OR EXISTING PR', 'Start with the goal', [
            '/kaizenflow <task>',
            'Or: /kaizenflow <PR> [quick|standard|deep]',
            'Task: build, then review. Existing PR: go to Review after framing.',
        ]),
        ('frame', 'ONE MESSAGE', 'Close blocking gaps', [
            'Ask only what blocks the work. Put other assumptions in the PR body.',
            'State the depth and its reason in one line.',
        ]),
        ('depth', 'JUDGEMENT', 'Set the review depth', [
            'quick: a mistake is visible and cheap to undo.',
            'standard: the default.',
            'deep: a mistake is costly or hidden.',
            'User depth is the minimum. In doubt, go one level deeper.',
        ]),
    ]),
    ('BUILD', 'The same context builds and fixes.', [
        ('prepare', 'BRANCH AND CAUSE', 'Prepare the change', [
            'Work on a branch. Use a worktree if the primary checkout is dirty or in use.',
            'Bug: reproduce it and find the cause first.',
            'deep: write “x over y, and why” in the PR body. Measure the deciding fact if cheap.',
        ]),
        ('author', 'THIS SESSION', 'Build the change', [
            'Build here. Use one fresh builder only if the work will clearly fill this context.',
            'Builder inputs: goal, worktree, branch. Return: PR URL, head SHA, proof.',
            'Keep the same builder for fixes.',
        ]),
        ('proof', 'PROOF AND PR', 'Check, then push', [
            'Run targeted tests during the work.',
            'Run $HOME/ai/scripts/kaizen-checks.sh before the first push. CI runs it too.',
            'PR body: goal, acceptance criteria, safety fact, and its proof.',
        ]),
    ]),
    ('REVIEW', 'Choose one route. Bind every independent report to the current head SHA.', [
        ('quick', 'QUICK · NO AGENT', 'Read your own diff', [
            'Read the diff once. Start no reviewer agent.',
            'Suitable examples: docs, comments, renames, and mechanical edits.',
            'Continue to Fix or Merge as needed.',
        ]),
        ('standard', 'STANDARD · ONE REVIEWER', 'Get a fresh review', [
            'Start kaizen-reviewer with PR number, worktree path, and head SHA.',
            'Give no opinion about the change. Prefer a model that did not write the code.',
            'A report for another head is void.',
        ]),
        ('deep', 'DEEP · TWO REVIEWERS', 'Review in parallel', [
            'Two fresh reviewers use different models and the same head SHA.',
            'Use for concurrency, stored or wire data, auth, secrets, migrations, or an unknown design.',
            'Apply the same report rules.',
        ]),
    ]),
    ('FIX', 'Check findings in the code. Keep the author context.', [
        ('fix', 'AUTHOR OR SAME BUILDER', 'Fix or rebut', [
            'Check each blocker and major. Fix minimally, or rebut with evidence.',
            'When cheap, add a test that fails without the fix. Rerun kaizen-checks.sh.',
            'For an existing PR, this session fixes.',
        ]),
        ('failed', 'FAILED CHECK = BLOCKER', 'Read the failed log', [
            'Fix the cause. At most one fix pass for failed checks.',
            'If the log proves this PR did not cause the failure, rerun that job once.',
            'Still open after the allowed pass: stop for manual handling.',
        ]),
        ('round2', 'CONDITIONAL · ONE REVIEWER', 'Decide on round 2', [
            'Only if a fix reaches beyond the faulty lines, touches callers, or rebuts a blocker.',
            'State the decision in one line. Pass old SHA, findings, and outcomes.',
            'Review the delta, fixes, and callers. No round 3.',
        ]),
    ]),
    ('MERGE', 'Resolve findings and user issues before the mechanical merge gate.', [
        ('user', 'FINAL PR READ', 'Check the conversation', [
            'Read: gh pr view <PR> --comments',
            'Treat each user-raised issue as a finding.',
            'If review found anything, post one comment: findings, outcomes, and unreviewed commits.',
            'Update the branch if the base changed code that the PR depends on.',
        ]),
        ('gate', 'SCRIPT ONLY', 'Wait for CI', [
            'Run kaizen-merge.sh <PR> <head SHA> in the background. Wait once; do not poll.',
            'Check registration: up to six attempts, 10 seconds apart.',
            'CI wait limit: 2,700 seconds. Final buckets must be pass or skipping.',
            '--no-ci: only if no workflow covers the files. Then kaizen-checks.sh --all, or the full repository check without .kaizen-checks, must pass first.',
        ]),
        ('merge', 'EXACT HEAD', 'Merge the checked head', [
            'The script runs gh pr merge with --merge --match-head-commit <SHA>.',
            'Failed or cancelled checks stop the merge. Missing checks stop the normal CI route.',
            'No --admin, force push, or push to the base branch.',
        ]),
    ]),
    ('FINISH', 'Every exit, including a stop, records a retrospective.', [
        ('retro', 'ONE TSV ROW', 'Record the outcome', [
            'State directory: kaizenflow/<owner>-<repo>.tsv',
            'Columns: date, task_or_pr, depth, reviewers, rounds, blockers, majors, outcome, lesson.',
            'Create the header for a new file.',
        ]),
        ('lesson', 'ONE SUBTRACTION', 'Record the lesson', [
            'lesson: one step or rule to remove or change next time, or “-”.',
            'State root: ${XDG_STATE_HOME:-$HOME/.local/state}',
            'Ambiguous result: stop and report.',
        ]),
        ('report', 'AT MOST FIVE LINES', 'Give the final report', [
            'PR URL; depth and reason; rounds; findings and outcomes; merge SHA or open issues.',
            'Name any commits that had no review.',
        ]),
    ]),
]

SIDEBAR = [
    ('HARD LIMITS', 'Stop and report', [
        'Never merge with an open blocker or major, an open user-raised critical issue, or a failed or cancelled check.',
        'At most two review rounds. At most one fix pass for failed checks.',
        'If an issue remains after the allowed limit, stop for manual handling.',
        'Stop on an ambiguous result.',
        'Reviewers never edit. No step starts /kaizenflow or /loomflow.',
    ]),
    ('REVIEWER CONTRACT', 'Read only; confirm defects', [
        'Read PR title, body, diff, and only the surrounding code needed.',
        'Check claims and acceptance proof, the safety fact, callers, failures, empty and maximum inputs, restart, and concurrency.',
        'Check tests, dead code after removals, and repository rules. For C++, use cpp-checklist.',
        'Disprove each suspected defect first. Report only a confirmed input and wrong result.',
        'No builds, tests, edits, PR comments, or agents. At most five findings, most severe first.',
        'Return Head: <SHA>, then R<round>-<i> [blocker|major] <path>:<line> with scenario and fix direction. Or: No findings.',
    ]),
    ('SEVERITY', 'Only blockers and majors', [
        'blocker: wrong behavior, crash, data loss, security issue, build break, or broken repository rule.',
        'major: likely defect, or changed behavior with no test.',
        'Skip style, naming, speculation, and untouched code.',
    ]),
    ('CONTEXT BUDGET', 'Reduce calls and handoffs', [
        'Batch independent commands. Find first, then read only the needed function. Limit output.',
        'Keep screenshots and browser snapshots out of this context. Delegate UI proof; return short facts.',
        'Do not repeat reports. Pass them on or act on them.',
        'Use skill questions as nudges. Read the skill only when the question does not settle the matter.',
        'Only Hard limits are flow rules. Other steps are defaults; state a reason in one line to change one. Repository rules still apply.',
    ]),
    ('SCOPE', 'Use LoomFlow for larger flows', [
        'KaizenFlow has no Major series, design rounds, or two design tracks.',
        'Operating sources: command, reviewer, and merge script. docs/kaizenflow.md records rationale and verification.',
    ]),
]


def wrap(text, columns=43):
    return textwrap.wrap(text, columns, break_long_words=True, break_on_hyphens=False)


def generate():
    body = []
    boxes = []

    def text(x, y, value, css):
        body.append(f'<text x="{x}" y="{y}" class="{css}">{escape(value)}</text>')

    def card(key, x, y, width, height, tag, title, paragraphs):
        boxes.append((key, x, y, width, height))
        body.append(f'<g id="{key}"><rect x="{x}" y="{y}" width="{width}" height="{height}" rx="12" class="card"/>')
        text(x + 16, y + 26, tag, 'tag')
        text(x + 16, y + 56, title, 'title')
        cursor = y + 84
        for paragraph in paragraphs:
            for line in wrap(paragraph):
                text(x + 16, cursor, line, 'detail')
                cursor += 19
            cursor += 10
        assert cursor - 10 <= y + height - 10, key
        body.append('</g>')

    def needed(paragraphs):
        return 94 + sum(len(wrap(p)) * 19 + 10 for p in paragraphs)

    y = 126
    centers = []
    for index, (name, subtitle, cards) in enumerate(STAGES, 1):
        height = max(needed(c[3]) for c in cards)
        band_height = height + 100
        body.append(f'<rect x="52" y="{y}" width="1140" height="{band_height}" rx="18" class="band b{index}"/>')
        text(82, y + 32, f'{index:02}  {name}', 'stage')
        text(82, y + 57, subtitle, 'subtitle')
        for col, (key, tag, title, paragraphs) in enumerate(cards):
            card(key, COLS[col], y + 78, CARD_WIDTH, height, tag, title, paragraphs)
        centers.append((y, y + band_height))
        y += band_height + 54

    # Stage connectors describe the common path; the review cards are alternatives.
    labels = ['task → build · existing PR → stage 3', 'push → review at the selected depth',
              'findings or failed checks → fix · otherwise → merge',
              'round 2 only when required; otherwise → merge', 'merged or stopped → record the outcome']
    for index, label in enumerate(labels):
        top = centers[index][1]
        bottom = centers[index + 1][0]
        body.append(f'<path d="M 622 {top} V {bottom - 4}" class="edge"/>')
        text(640, top + 31, label, 'route')

    # One return edge makes the second review round visible without duplicating it.
    review_y = centers[2][0] + 160
    fix_y = centers[3][0] + 160
    body.append(f'<path d="M 52 {fix_y} H 22 V {review_y} H 48" class="edge loop"/>')
    body.append(f'<text x="16" y="{(review_y + fix_y) // 2}" class="route" transform="rotate(-90 16 {(review_y + fix_y) // 2})">Round 2 · one reviewer · delta + callers</text>')

    side_y = 126
    for index, (tag, title, paragraphs) in enumerate(SIDEBAR):
        height = needed(paragraphs)
        card(f'policy-{index}', 1224, side_y, CARD_WIDTH, height, tag, title, paragraphs)
        side_y += height + 24

    height = max(y, side_y) + 90
    text(52, height - 64, 'Regenerate: python3 scripts/generate-kaizenflow-diagram.py · Verify freshness: add --check', 'subtitle')
    text(52, height - 38, 'Sources: claude/commands/kaizenflow.md · claude/agents/kaizen-reviewer.md · scripts/kaizen-merge.sh', 'subtitle')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}" role="img" aria-labelledby="title desc">
<title id="title">KaizenFlow — detailed build and review workflow</title>
<desc id="desc">Six stages: Frame, Build, Review, Fix, Merge, Finish. Three review depths, conditional second review, exact-head merge, stop conditions, reviewer contract, and retrospective. Cards within a stage describe work or alternatives, not separate agent handoffs. Existing PRs skip Build. Every stop reaches Finish.</desc>
<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M 0 0 L 10 5 L 0 10 z" fill="context-stroke"/></marker></defs>
<style>
:root {{ --bg:var(--background,#ffffff); --fg:var(--foreground,#172033); --sub:var(--muted-foreground,#526174); --box:var(--card,#f6f8fc); --line:var(--border,#cbd5e1); --flow:var(--primary,#285cce); --fix:var(--warning,#9b6500) }}
@media(prefers-color-scheme:dark) {{ :root {{ --bg:var(--background,#101720); --fg:var(--foreground,#e6edf3); --sub:var(--muted-foreground,#abb8ca); --box:var(--card,#192330); --line:var(--border,#435267); --flow:var(--primary,#8aafff); --fix:var(--warning,#f3bb55) }} }}
.canvas {{fill:#ffffff;fill:var(--bg)}} text {{font-family:Arial,sans-serif;fill:#172033;fill:var(--fg)}}
.heading {{font-size:36px;font-weight:750}} .subtitle {{font-size:16px;fill:#526174;fill:var(--sub)}}
.band {{fill:#3971ed0b;stroke:#cbd5e1;stroke:var(--line)}} .b4 {{fill:#bc77000c}} .b5,.b6 {{fill:#1599770b}}
.card {{fill:#f6f8fc;fill:var(--box);stroke:#cbd5e1;stroke:var(--line);stroke-width:1.2}}
.stage {{font-size:21px;font-weight:750;letter-spacing:1px}} .tag {{font-size:12px;font-weight:700;fill:#285cce;fill:var(--flow);letter-spacing:.7px}}
.title {{font-size:21px;font-weight:700}} .detail {{font-size:14px;fill:#172033;fill:var(--fg)}}
.edge {{fill:none;stroke:#285cce;stroke:var(--flow);stroke-width:2;marker-end:url(#arrow)}}
.loop {{stroke:#9b6500;stroke:var(--fix);stroke-dasharray:6 4}} .route {{font-size:13px;fill:#526174;fill:var(--sub)}}
</style>
<rect width="{WIDTH}" height="{height}" class="canvas"/>
<text x="52" y="53" class="heading">KaizenFlow</text>
<text x="52" y="84" class="subtitle">One context builds and fixes · fresh review by depth · one script merges · a lesson on every exit</text>
{''.join(body)}
</svg>
'''
    root = ET.fromstring(svg)
    ns = {'s': 'http://www.w3.org/2000/svg'}
    assert len(root.findall('s:g', ns)) == len(boxes)
    assert len({box[0] for box in boxes}) == len(boxes)
    for _, x, top, width, box_height in boxes:
        assert 0 <= x < x + width <= WIDTH
        assert 0 <= top < top + box_height <= height
    return svg


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Fail if the SVG is stale; do not write.')
    args = parser.parse_args()
    svg = generate().encode('utf-8')
    if args.check:
        if not OUT.exists() or OUT.read_bytes() != svg:
            parser.exit(1, 'KaizenFlow SVG is stale. Run this generator without --check.\n')
        print('KaizenFlow SVG is current; XML, card bounds, and IDs checked.')
    else:
        OUT.write_bytes(svg)
        print(f'Generated {OUT}; XML, card bounds, and IDs checked.')
