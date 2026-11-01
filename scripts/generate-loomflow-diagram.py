#!/usr/bin/env python3
"""Generate docs/loomflow.svg. Run: python3 scripts/generate-loomflow-diagram.py

The SVG is a view. docs/loomflow.md is the source of truth.
Each node appears once. A repeated step (review round 2, the final analyzer)
is a loop edge to the same node, not a copy."""
from html import escape
from pathlib import Path
import xml.etree.ElementTree as ET

OUT = Path(__file__).resolve().parent.parent / 'docs' / 'loomflow.svg'
W = 1424
CW, CH, PITCH = 240, 90, 120          # card width, card height, row pitch
COLS = [172, 436, 700, 964]           # card columns
PAD, GAP = 14, 28                     # band padding, gap between bands
BAND_X, BAND_W = 12, 1248
LANE_X, LANE_W = 1280, 130            # stop lane

# (number, name, note, rows, tint class)
STAGES = [
    ('1', 'DEFINE', 'build mode', 1),
    ('2', 'BUILD', 'build mode', 2),
    ('3', 'PREPARE', 'review mode', 1),
    ('4', 'REVIEW', 'rounds 1 and 2', 2),
    ('5', 'FIX', 'analyzer', 1),
    ('6', 'FINISH', 'gate, merge, retro', 1),
]
HEADER = 138
band_y, y = [], HEADER
for _, _, _, rows in STAGES:
    h = 2 * PAD + (rows - 1) * PITCH + CH
    band_y.append((y, h))
    y += h + GAP
FOOT = y - GAP + 30
H = FOOT + 112

def bus(stage):
    """Y of the gap line below a stage (1-based)."""
    top, h = band_y[stage - 1]
    return top + h + GAP // 2

parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">
<title id="title">LoomFlow — build and review workflow</title>
<desc id="desc">Six stages. Define: refine the requirement and size the change. Build: Small and Normal builds go straight to a PR; Major builds add a design note and design review. Prepare: verify the PR and select the scan or full review. Review: scan, or two full reviewers, then validate the reports and checks. Fix: one analyzer fixes or rebuts findings and failed checks; round 2 reuses the review stage once. Finish: one merge gate, then the merge, then the retrospective; every exit, including a stop, records it.</desc>
<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="context-stroke"/></marker></defs>
<style>
:root {{ --fg:var(--foreground,#172033); --mute:var(--muted-foreground,#58667b); --card-bg:var(--card,#f5f7fb); --blue:var(--primary,#3971ed); --amber:var(--warning,#bc7700); --red:var(--destructive,#cf4051) }}
@media(prefers-color-scheme:dark) {{ :root {{ --fg:var(--foreground,#e6edf3); --mute:var(--muted-foreground,#9aa7b8); --card-bg:var(--card,#1a212c); --amber:var(--warning,#e0a030); --red:var(--destructive,#f06a78) }} }}
text {{ font-family:Inter,Arial,sans-serif; fill:var(--fg) }}
.heading {{ font-size:32px;font-weight:750;letter-spacing:-1px }}
.caption {{ font-size:15px;fill:var(--mute) }}
.label {{ font-size:13px;fill:var(--mute);font-weight:600 }}
.elabel {{ font-size:11px;fill:var(--mute);font-weight:600 }}
.elabel.fix {{ fill:var(--amber) }}
.elabel.stop {{ fill:var(--red) }}
.band {{ stroke-width:1 }}
.b1,.b2 {{ fill:#2563eb12;stroke:#2563eb40 }}
.b3,.b4,.b5 {{ fill:#7c3aed10;stroke:#7c3aed38 }}
.b6 {{ fill:#0f9d7a12;stroke:#0f9d7a40 }}
.snum {{ fill:var(--fg);opacity:.9 }}
.snumtext {{ font-size:15px;font-weight:800;fill:var(--card-bg);text-anchor:middle }}
.sname {{ font-size:17px;font-weight:800;letter-spacing:.5px }}
.snote {{ font-size:12px;fill:var(--mute);font-weight:600 }}
.card {{ fill:var(--card-bg);stroke:color-mix(in srgb,var(--fg) 26%,transparent);stroke-width:1.5 }}
.card.cond {{ stroke-dasharray:6 5 }}
.card.fix {{ stroke:var(--amber) }}
.lane {{ fill:color-mix(in srgb,var(--red) 8%,transparent);stroke:var(--red);stroke-width:1.5 }}
.name {{ font-size:17px;font-weight:700 }}
.detail {{ font-size:13px;fill:var(--mute) }}
.tag {{ font-size:11px;font-weight:750;letter-spacing:.8px;fill:var(--blue) }}
.lanetag {{ font-size:11px;font-weight:750;letter-spacing:.8px;fill:var(--red) }}
.edge {{ fill:none;stroke:var(--mute);stroke-width:2;marker-end:url(#arrow) }}
.cond {{ stroke-dasharray:5 6 }}
.edge.fix {{ stroke:var(--amber) }}
.edge.stop {{ stroke:var(--red) }}
.pulse {{ fill:none;stroke:var(--blue);stroke-width:2.5;opacity:0;animation:light 24s linear infinite }}
.dot {{ fill:var(--blue);opacity:.85 }}
@keyframes light {{ 0%,6%,100% {{opacity:0}} 1%,4% {{opacity:1}} }}
@media(prefers-reduced-motion:reduce) {{ .pulse {{animation:none}} .dot {{display:none}} }}
</style>
<text x="25" y="43" class="heading">LoomFlow</text>
<text x="25" y="73" class="caption">Build a task or review a PR · refine, size, build, review, one fixer, one gate</text>
<circle cx="32" cy="102" r="5" class="dot"/><text x="47" y="107" class="label">Animated flow</text>
<path d="M 190 102 H 230" class="edge cond"/><text x="240" y="107" class="label">Conditional path</text>
<path d="M 400 102 H 440" class="edge fix"/><text x="450" y="107" class="label">Fix / round 2</text>
<path d="M 590 102 H 630" class="edge stop"/><text x="640" y="107" class="label">Stop</text>
<text x="1400" y="43" text-anchor="end" class="label">AUTOPILOT BY DEFAULT</text>
''']

# ---- cards -----------------------------------------------------------
cards = {}   # key -> (x, y, w, h)
nodes = []

def card(key, stage, col, row, tag, name, lines, delay, tone='', span=1):
    top, _ = band_y[stage - 1]
    x = COLS[col]
    w = CW * span + 24 * (span - 1)
    cards[key] = (x, top + PAD + row * PITCH, w, CH)
    nodes.append((key, tag, name, lines, delay, tone))

def T(key, dx=0):
    x, y, w, h = cards[key]; return (x + w / 2 + dx, y)
def B(key, dx=0):
    x, y, w, h = cards[key]; return (x + w / 2 + dx, y + h)
def L(key, dy=0):
    x, y, w, h = cards[key]; return (x, y + h / 2 + dy)
def R(key, dy=0):
    x, y, w, h = cards[key]; return (x + w, y + h / 2 + dy)

# 1 DEFINE
card('start', 1, 0, 0, 'ENTRY · BUILD MODE', 'Start LoomFlow', ['/loomflow <task>', 'Autopilot unless supervised.'], 0)
card('requirement', 1, 1, 0, 'REQUIREMENT · FIVE Cs', 'Refine the requirement', ['Ask every gap in one message.', 'Record assumptions + criteria.'], 1)
card('size', 1, 2, 0, 'SIZING · ORCHESTRATOR', 'Size the change', ['Small, Normal, or Major.', 'Review mode keeps a larger size.'], 2)
# 2 BUILD
card('build-sn', 2, 0, 0, 'SMALL · NORMAL', 'Delegate the build', ['Builder checks and opens the PR.', 'Major only by path = Normal.'], 3)
card('draft', 2, 2, 0, 'MAJOR · BUILDER', 'Draft the design note', ['Draft PR: x over y, deletions,', 'and the one safety fact.'], 3)
card('design', 2, 3, 0, 'DESIGN REVIEW', 'Review the design', ['Blocker/major → revise once.', 'R2 only if a blocker is open.'], 4, 'cond')
card('build-major', 2, 3, 1, 'MAJOR · BUILDER', 'Build and prove', ['Safety fact + proof in PR body.', 'Mark the PR ready.'], 5)
card('series', 2, 1, 1, 'MAJOR SERIES · MORE THAN ONE PR', 'PRs target a feature branch', ['Local check gates; CI runs cancelled; trail file.', 'Redesign series: stop after the last merge; user tests.'], 5, 'cond', span=2)
# 3 PREPARE
card('entry', 3, 0, 0, 'REVIEW MODE ENTRY', 'Existing PR', ['/loomflow <PR> [full|scan]', 'Skip requirement and build.'], 0, 'cond')
card('setup', 3, 1, 0, 'SETUP · ORCHESTRATOR', 'Verify the PR', ['Open PR · HEAD = headRefOid.', 'Clean worktree · fetch base.'], 6)
card('triage', 3, 2, 0, 'TRIAGE · ORCHESTRATOR', 'Select the review tier', ['Scan only for small, safe diffs.', 'Sensitive path or doubt → full.'], 7)
# 4 REVIEW
card('scan', 4, 0, 0, 'SCAN', 'One quick reviewer', ['Validate the report, then:', 'none → checks; else full.'], 8, 'cond')
card('full', 4, 0, 1, 'FULL · ROUND 1 OR 2', 'Reviewers A + B', ['Same head SHA, in parallel.', 'Round 2: fixes + new commits.'], 8)
card('validate', 4, 1, 0.5, 'ORCHESTRATOR', 'Validate the reports', ['PR, mode, round, SHA match.', 'Bad or missing report → stop.'], 9)
card('checks', 4, 2, 0.5, 'CHECKS', 'Reuse + watch checks', ['Reuse passing results; watch CI.', 'A failed check is a blocker.'], 10)
# 5 FIX
card('analyzer', 5, 0, 0, 'ANALYZER · ONE', 'Fix or rebut', ['Every finding and failed check.', 'Test first · push · report IDs.'], 11, 'fix')
card('open', 5, 1, 0, 'HEAD SAME, OR AFTER ROUND 2', 'Anything still open?', ['Blocker, major, user critical?', 'No → gate. Yes → stop.'], 12)
# 6 GATE
card('gate', 6, 1, 0, 'TEST AND MERGE · ONCE', 'Run the merge gate', ['SHA · clean tree · reuse · CI.', 'MERGEABLE + CLEAN, no retry.'], 13)
card('merge', 6, 2, 0, 'PASS', 'Merge the head', ['gh merge --match-head-commit.', 'Never --admin or force.'], 14)
# 7 CLOSE
card('retro', 6, 3, 0, 'EVERY EXIT', 'Record the retro', ['One TSV row, also on a stop.', 'Then the final report.'], 15)

# ---- edges -----------------------------------------------------------
edges = []   # drawn before the cards so that the connectors stay behind them

def route(pts, r=8):
    d = f'M {pts[0][0]:g} {pts[0][1]:g}'
    for i in range(1, len(pts) - 1):
        (x0, y0), (x1, y1), (x2, y2) = pts[i - 1], pts[i], pts[i + 1]
        l1 = abs(x1 - x0) + abs(y1 - y0); l2 = abs(x2 - x1) + abs(y2 - y1)
        k1 = min(r, l1 / 2) / l1; k2 = min(r, l2 / 2) / l2
        ax, ay = x1 - (x1 - x0) * k1, y1 - (y1 - y0) * k1
        bx, by = x1 + (x2 - x1) * k2, y1 + (y2 - y1) * k2
        d += f' L {ax:g} {ay:g} Q {x1:g} {y1:g} {bx:g} {by:g}'
    return d + f' L {pts[-1][0]:g} {pts[-1][1]:g}'

def edge(pts, kind='', animate=False):
    d = route(pts)
    edges.append(f'<path d="{d}" class="edge {kind}"/>')
    if animate:
        edges.append(f'<circle r="3.5" class="dot"><animateMotion dur="2.8s" repeatCount="indefinite" path="{d}"/></circle>')

def label(text, x, y, kind='', anchor='start'):
    edges.append(f'<text x="{x:g}" y="{y:g}" class="elabel {kind}" text-anchor="{anchor}">{escape(text)}</text>')

# DEFINE
edge([R('start'), L('requirement')], animate=True)
edge([R('requirement'), L('size')], animate=True)
# Size branches: Small/Normal go left, Major goes straight down.
b1 = bus(1)
edge([B('size', -70), (T('size', -70)[0], b1), (B('build-sn')[0], b1), T('build-sn')], 'cond', True)
label('Small / Normal', B('size', -78)[0], b1 - 4, anchor='end')
edge([B('size', 50), T('draft', 50)], 'cond')
label('Major', B('size', 58)[0], b1 + 4)
# BUILD (Major design loop)
edge([R('draft'), L('design')])
edge([B('design', 50), T('build-major', 50)])
label('clear or revised', B('design', 58)[0], B('design')[1] + 19)
by = B('design')[1] + 11
edge([B('design', -50), (B('design', -50)[0], by), (B('draft', 50)[0], by), B('draft', 50)], 'fix')
label('revise once', (B('design', -50)[0] + B('draft', 50)[0]) / 2, by + 13, 'fix', 'middle')
# Every build ends in a PR for review mode.
b2 = bus(2)
setup_in = T('setup')
edge([B('build-sn'), (B('build-sn')[0], b2), (setup_in[0], b2), setup_in], animate=True)
edge([B('build-major'), (B('build-major')[0], b2), (setup_in[0], b2), setup_in])
label('PR ready for review', B('build-sn')[0] + 8, b2 - 4)
# PREPARE
edge([R('entry'), L('setup')], 'cond')
edge([R('setup'), L('triage')], animate=True)
b3 = bus(3)
tb = B('triage')[1]
# full goes round the left of the scan card; scan goes straight down.
edge([B('triage', -50), (B('triage', -50)[0], tb + 20), (152, tb + 20), (152, L('full')[1]), L('full')], 'cond', True)
label('full', 600, tb + 16)
edge([B('triage', 50), (B('triage', 50)[0], tb + 36), (T('scan')[0], tb + 36), T('scan')], 'cond')
label('scan', 600, tb + 50)
# REVIEW
edge([B('scan', -30), T('full', -30)], 'fix')
label('validated findings: escalate', B('scan', -22)[0], B('scan')[1] + 19, 'fix')
sv = R('scan')
edge([sv, (T('validate')[0], sv[1]), T('validate')], 'cond')
label('scan report', R('scan')[0] + 14, sv[1] - 6)
fv = R('full')
edge([fv, (fv[0] + 12, fv[1]), (fv[0] + 12, L('validate')[1]), L('validate')], animate=True)
edge([R('validate'), L('checks')], animate=True)
# findings and failed checks both go to the one analyzer
b4 = bus(4)
an_in = T('analyzer', 60)
edge([B('validate', -30), (B('validate', -30)[0], b4), (an_in[0], b4), an_in], 'fix')
label('findings', B('validate', -38)[0], b4 - 4, 'fix', 'end')
edge([B('checks', -30), (B('checks', -30)[0], b4), (B('validate', -30)[0], b4)], 'fix')
label('failed check', B('checks', -38)[0], b4 - 4, 'fix', 'end')
# FIX
edge([T('analyzer', -90), B('full', -90)], 'fix')
label('round 2', T('analyzer', -82)[0], B('full')[1] + 24, 'fix')
label('if round 1 changed head', T('analyzer', -82)[0], B('full')[1] + 36, 'fix')
edge([R('analyzer'), L('open')], 'cond')
# Checks pass go to the gate; they cross the open-issue stop line once.
b5 = bus(5)
gate_in = T('gate')
edge([B('checks', 50), (B('checks', 50)[0], b5), (gate_in[0] + 40, b5), (gate_in[0] + 40, gate_in[1])], animate=True)
label('checks pass', B('checks', 58)[0], B('checks')[1] + 19)
edge([B('open', -40), T('gate', -40)])
label('none open', B('open', -32)[0], B('open')[1] + 24)
# FINISH: gate -> merge -> retro in one row
edge([R('gate'), L('merge')], animate=True)
edge([R('merge'), L('retro')], animate=True)

# Stop lane: one node. Every stop arrow joins it.
lane_top = band_y[1][0] + PAD
lane_bot = cards['gate'][1] + CH + 22
def stop(src, why):
    x, y = src
    edge([src, (LANE_X, y)], 'stop')
    for i, text in enumerate(why):
        label(text, (x + LANE_X) / 2, y - 14 + i * 12 - 12 * (len(why) - 1), 'stop', 'middle')
stop(R('design'), ['blocker open', 'after design', 'round 2'])
stop(R('open'), ['blocker/major open after', 'the final round, or user critical'])
# The gate stop runs under the merge and retro cards, so it crosses no arrow.
gy = cards['gate'][1] + CH + 8
edge([B('gate'), (B('gate')[0], gy), (LANE_X, gy)], 'stop')
label('gate failed: no retry', 1090, gy + 14, 'stop')
sy = b2 + 7
edge([B('series', 212), (B('series', 212)[0], sy), (LANE_X, sy)], 'stop')
label('series done: wait for user', 1090, sy + 14, 'stop')
rx, ry = R('retro')
edge([(LANE_X, ry), (rx, ry)], 'stop')
label('then retro', (rx + LANE_X) / 2, ry - 8, 'stop', 'middle')

parts.extend(edges[:0])  # placeholder to keep the draw order explicit below

# ---- bands and lane (behind the edges) --------------------------------
back = []
for i, (num, name, note, rows) in enumerate(STAGES):
    top, h = band_y[i]
    back.append(f'<rect x="{BAND_X}" y="{top}" width="{BAND_W}" height="{h}" rx="14" class="band b{num}"/>')
    cy = top + h / 2
    back.append(f'<circle cx="38" cy="{cy - 14:g}" r="14" class="snum"/><text x="38" y="{cy - 8.5:g}" class="snumtext">{num}</text>')
    back.append(f'<text x="28" y="{cy + 22:g}" class="sname">{name}</text>')
    back.append(f'<text x="28" y="{cy + 38:g}" class="snote">{note}</text>')
back.append(f'<rect x="{LANE_X}" y="{lane_top}" width="{LANE_W}" height="{lane_bot - lane_top}" rx="14" class="lane"/>')
ly = lane_top + 24
lane_lines = [('t', 'STOP'), ('n', 'Manual handling'), ('d', 'Report the open'), ('d', 'issue and the PR.'), ('g', ''),
              ('d', 'Also stops on:'), ('d', '· closed/merged PR'), ('d', '· setup mismatch'), ('d', '· bad or missing'), ('d', '  direct report'), ('d', '· ambiguous result'), ('d', '· read-only role'), ('d', '  changed HEAD'), ('d', '· redesign series'), ('d', '  done: user tests')]
for kind, text in lane_lines:
    if kind == 't':
        back.append(f'<text x="{LANE_X + 14}" y="{ly}" class="lanetag">{text}</text>'); ly += 24
    elif kind == 'n':
        back.append(f'<text x="{LANE_X + 14}" y="{ly}" class="name" style="font-size:14px">{text}</text>'); ly += 22
    elif kind == 'g':
        ly += 10
    else:
        back.append(f'<text x="{LANE_X + 14}" y="{ly}" class="detail" style="font-size:12px">{escape(text)}</text>'); ly += 17

parts.extend(back)
parts.extend(edges)

for key, tag, name, lines, delay, tone in nodes:
    x, y, w, h = cards[key]
    # A text line must fit the card: about 6.3 px per character at 13 px.
    for line in lines:
        assert len(line) * 6.3 <= w - 28, f'{key}: line too long: {line}'
    assert len(name) * 9.4 <= w - 28, f'{key}: name too long: {name}'
    parts.append(f'<g id="{key}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" class="card {tone}"/>')
    parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" class="pulse" style="animation-delay:{delay * 1.4:g}s"/>')
    parts.append(f'<text x="{x + 14}" y="{y + 19}" class="tag">{escape(tag)}</text>')
    parts.append(f'<text x="{x + 14}" y="{y + 42}" class="name">{escape(name)}</text>')
    for i, line in enumerate(lines):
        parts.append(f'<text x="{x + 14}" y="{y + 62 + i * 17}" class="detail">{escape(line)}</text>')
    parts.append('</g>')

parts.append(f'''<text x="25" y="{FOOT + 10}" class="caption">Supervised mode (only when asked): the user approves the requirement, the plan or design note, and the start of the gate.</text>
<text x="25" y="{FOOT + 34}" class="caption">At most two review rounds and one merge gate. No round 3, no second gate, no restart. Commits after the last review are reported as unreviewed.</text>
<text x="25" y="{FOOT + 58}" class="caption">Direct agent reports control the run. PR review and analyzer comments are audit copies. Only the user starts a run.</text>
<text x="25" y="{FOOT + 86}" class="label">Source: docs/loomflow.md (canonical) · generated by scripts/generate-loomflow-diagram.py</text>
</svg>''')
svg = '\n'.join(parts)
root = ET.fromstring(svg)
ns = {'s': 'http://www.w3.org/2000/svg'}
assert len(root.findall('s:g', ns)) == len(nodes)
assert len({node[0] for node in nodes}) == len(nodes)
assert root.findall('.//s:animateMotion', ns)
OUT.write_bytes((svg + '\n').encode('utf-8'))
print(f'Generated {OUT}: {len(nodes)} named boxes; SVG XML and animation paths checked.')
