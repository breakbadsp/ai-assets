#!/usr/bin/env python3
"""Generate docs/loomflow.svg. Run: python3 scripts/generate-loomflow-diagram.py

The SVG is a view. docs/loomflow.md is the source of truth."""
from html import escape
from pathlib import Path
import xml.etree.ElementTree as ET

OUT = Path(__file__).resolve().parent.parent / 'docs' / 'loomflow.svg'
W, H = 1080, 1900
parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">
<title id="title">LoomFlow — current build and review workflow</title>
<desc id="desc">Build mode starts with requirement refinement. An existing PR enters at setup. Major feature builds include design review. Scan findings escalate to full review. Full review has at most two rounds, followed by one merge gate. Every exit records a retrospective.</desc>
<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="context-stroke"/></marker></defs>
<style>
text {{ font-family:Inter,Arial,sans-serif; fill:var(--foreground,#172033) }}
.heading {{ font-size:32px;font-weight:750;letter-spacing:-1px }}
.caption {{ font-size:16px;fill:var(--muted-foreground,#58667b) }}
.label {{ font-size:14px;fill:var(--muted-foreground,#58667b);font-weight:600 }}
.card {{ fill:var(--card,#f5f7fb);stroke:color-mix(in srgb,var(--foreground,#172033) 24%,transparent);stroke-width:1.5 }}
.name {{ font-size:20px;font-weight:700 }}
.detail {{ font-size:15px;fill:var(--muted-foreground,#58667b) }}
.tag {{ font-size:12px;font-weight:750;letter-spacing:1px;fill:var(--info,#2563eb) }}
.edge {{ fill:none;stroke:var(--muted-foreground,#718096);stroke-width:2;marker-end:url(#arrow) }}
.optional {{ stroke-dasharray:5 6 }}
.fix {{ stroke:var(--warning,#bc7700) }}
.stop {{ stroke:var(--destructive,#cf4051) }}
.pulse {{ fill:none;stroke:var(--primary,#3971ed);stroke-width:2.5;opacity:0;animation:light 20s linear infinite }}
.dot {{ fill:var(--primary,#3971ed);opacity:.85 }}
@keyframes light {{ 0%,7%,100% {{opacity:0}} 1%,5% {{opacity:1}} }}
@media(prefers-reduced-motion:reduce) {{ .pulse {{animation:none}} .dot {{display:none}} }}
</style>
<text x="25" y="43" class="heading">LoomFlow</text>
<text x="25" y="73" class="caption">Current workflow · build a task or review an existing PR</text>
<circle cx="32" cy="102" r="5" class="dot"/><text x="47" y="107" class="label">Animated flow</text>
<path d="M 225 102 H 265" class="edge optional"/><text x="278" y="107" class="label">Conditional path</text>
<path d="M 460 102 H 500" class="edge fix"/><text x="513" y="107" class="label">Fix / review again</text>
<text x="1055" y="43" text-anchor="end" class="label">AUTOPILOT BY DEFAULT</text>
''']

def edge(path, kind='', label=None, xy=None, animate=False):
    parts.append(f'<path d="{path}" class="edge {kind}"/>')
    if label:
        parts.append(f'<text x="{xy[0]}" y="{xy[1]}" class="label">{escape(label)}</text>')
    if animate:
        parts.append(f'<circle r="3.5" class="dot"><animateMotion dur="2.8s" repeatCount="indefinite" path="{path}"/></circle>')

nodes = []
def box(key, x, y, width, tag, name, lines, delay=0, tone=''):
    nodes.append((key,x,y,width,tag,name,lines,delay,tone))

box('start',330,135,420,'ENTRY','Start LoomFlow',['User supplies a task or an existing PR.'],0)
box('requirement',330,245,420,'01 · BUILD MODE','Refine the requirement',['Five Cs · resolve gaps with the user.','Record acceptance criteria and assumptions.'],1)
box('size',330,355,420,'02 · ORCHESTRATOR','Size the change',['Small / Normal / Major','Select the builder, reviewers, and effort.'],2)
box('design',330,465,420,'03 · MAJOR FEATURE / REDESIGN / >300 CODE LINES','Draft the design',['Builder opens a draft PR with the design.','Other builds go directly to Build + prove.'],3)
box('design-review',805,465,250,'DESIGN REVIEW','Review the design',['Revise once if needed.','Round 2 only for blockers.'],3,'optional')
box('build',330,575,420,'04 · BUILDER','Build + prove',['Implement the acceptance criteria.','Run checks and record the safety proof.'],4)
box('pr',330,685,420,'05 · BUILDER','Open / ready the PR',['Keep the Requirement block in the body.','Push the code and confirm the head SHA.'],5)
box('existing',25,685,250,'REVIEW MODE ENTRY','Existing PR',['Skip requirement and build.','Use the supplied PR.'],0)
box('setup',330,795,420,'06 · ORCHESTRATOR','Verify PR setup',['Open PR · correct head SHA','Clean PR worktree · fetch the base.'],6)
box('triage',330,905,420,'07 · ORCHESTRATOR','Select the review tier',['Scan only for eligible low-risk changes.','Sensitive paths or doubt require full.'],7)
box('scan',110,1015,380,'08A · SCAN','One quick reviewer',['No findings → checks. Findings → full R1.'],8)
box('full',590,1015,380,'08B · FULL','Two reviewers in parallel',['Reviewer A + B review the same head SHA.'],8)
box('findings',330,1125,420,'09 · ORCHESTRATOR','Assess direct reports',['Match PR, round, mode, and head SHA.','Pass complete findings to the analyzer.'],9)
box('analyze',805,1235,250,'10 · IF FINDINGS','Analyze + fix / rebut',['One analyzer handles findings','and each failed CI check.'],10,'fix')
box('round2',805,1345,250,'11 · IF ROUND 1 CHANGES HEAD','Review round 2',['Review fixes and new commits.','Check their callers. No R3.'],11,'fix')
box('analyze2',805,1455,250,'FINAL ANALYZER · IF FINDINGS','Analyze round 2',['Fix or rebut; no third review.','Clear → checks; open → stop.'],12,'fix')
box('checks',330,1345,420,'12 · NO OPEN FINDINGS','Reuse checks + verify CI',['Reuse passing checks for combined inputs.','Stop at the first failed check.'],12)
box('gate',330,1455,420,'13 · TEST AND MERGE · ONCE','Run the merge gate',['Expected SHA · clean worktree · coverage','Mergeable + clean · respect branch checks.'],13)
box('merge',330,1565,420,'14 · PASS','Merge the reviewed head',['Use --match-head-commit.','No --admin, force, or gate retry.'],14)
box('stop',805,1565,250,'STOP · MANUAL HANDLING','Report and stop',['Open issues after round 2,','failed gate, or failed checks.'],14,'stop')
box('retro',330,1675,420,'15 · EVERY EXIT','Record the retrospective',['Append outcome, models, and one lesson.','This also applies to stops and failures.'],15)

# Draw routes first so that connectors stay behind the cards.
for y in [135,245,355,465,575,685,795]:
    edge(f'M 540 {y+86} V {y+110}',animate=True)
edge('M 330 178 H 150 V 685','optional', 'PR input', (53,475))
edge('M 275 728 H 300 V 838 H 330',animate=True)
edge('M 750 508 H 805','optional')
edge('M 930 551 V 610 H 750','optional')
edge('M 330 398 H 305 V 618 H 330','optional')
edge('M 430 991 V 1003 H 300 V 1015',label='scan',xy=(438,1001))
edge('M 650 991 V 1003 H 780 V 1015',label='full',xy=(612,1001))
edge('M 300 1101 V 1168 H 330')
edge('M 780 1101 V 1168 H 750',animate=True)
edge('M 490 1044 H 590','fix', 'escalate',(497,1034))
edge('M 540 1211 V 1345',label='No open findings',xy=(553,1287),animate=True)
edge('M 750 1168 H 930 V 1235','fix', 'Findings',(828,1205))
edge('M 930 1321 V 1345','fix')
edge('M 805 1278 H 770 V 1310 H 700 V 1345','optional')
edge('M 805 1370 H 750','optional')
edge('M 930 1431 V 1455','fix')
edge('M 805 1478 H 775 V 1418 H 750','optional')
edge('M 930 1541 V 1565','stop','Open after fix',(943,1558))
edge('M 750 1498 H 790 V 1608 H 805','stop','Gate failed',(650,1555))
edge('M 750 1400 H 790 V 1587 H 805','stop','Check failed',(650,1445))
edge('M 540 1431 V 1455',animate=True)
edge('M 540 1541 V 1565',animate=True)
edge('M 540 1651 V 1675',animate=True)
edge('M 930 1651 V 1718 H 750','optional')

for key,x,y,width,tag,name,lines,delay,tone in nodes:
    parts.append(f'<g id="{key}"><rect x="{x}" y="{y}" width="{width}" height="86" rx="12" class="card {tone}"/>')
    parts.append(f'<rect x="{x}" y="{y}" width="{width}" height="86" rx="12" class="pulse" style="animation-delay:{delay}s"/>')
    # Long phase tags use a smaller font to keep every label inside its box.
    tag_size = ' style="font-size:10px"' if len(tag)>35 else ''
    parts.append(f'<text x="{x+16}" y="{y+19}" class="tag"{tag_size}>{escape(tag)}</text>')
    parts.append(f'<text x="{x+16}" y="{y+43}" class="name">{escape(name)}</text>')
    for i,line in enumerate(lines):
        parts.append(f'<text x="{x+16}" y="{y+62+i*17}" class="detail">{escape(line)}</text>')
    parts.append('</g>')

parts.append('''<text x="938" y="585" class="label" style="font-size:12px">Blocker after R2 → stop</text>
<text x="25" y="1801" class="caption">Supervised mode: approve the requirement, plan or design, and start of the gate.</text>
<text x="25" y="1826" class="caption">Major redesign series: user tests the feature branch before the final sync PR.</text>
<text x="25" y="1851" class="caption">Direct reports control the run. PR review and analyzer comments are audit copies.</text>
<text x="25" y="1876" class="label">Source: docs/loomflow.md (canonical) · generated by scripts/generate-loomflow-diagram.py</text>
</svg>''')
svg = '\n'.join(parts)
root = ET.fromstring(svg)
ns = {'s':'http://www.w3.org/2000/svg'}
assert len(root.findall('s:g',ns)) == len(nodes)
assert len({node[0] for node in nodes}) == len(nodes)
assert root.findall('.//s:animateMotion',ns)
OUT.write_bytes((svg + '\n').encode('utf-8'))
print(f'Generated {OUT}: {len(nodes)} named boxes; SVG XML and animation paths checked.')
