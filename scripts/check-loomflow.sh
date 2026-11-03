#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
spec="$root/docs/loomflow.md"
command="$root/claude/commands/loomflow.md"
for file in "$spec" "$command"; do
  test -s "$file"
done
for role in pr-builder pr-adversarial-reviewer pr-quick-reviewer pr-comment-analyzer pr-test-merger; do
  test -s "$root/claude/agents/$role.md"
  grep -Fq '"Agent communication"' "$root/claude/agents/$role.md"
done
grep -Fxq '## Agent communication' "$spec"
grep -Fq '"Agent communication"' "$command"
! grep -q 'Haiku' "$spec" "$command"
# Check the LoomFlow role settings.
if grep -En 'Opus 5\.5[, ]+`?high|Sol `?xhigh|effort: (xhigh|max|ultra)' \
  "$spec" "$command" "$root"/claude/agents/*.md; then
  printf 'Reasoning settings exceed the policy.\n' >&2
  exit 1
fi
# Model policy: the orchestrator picks the model and effort of each role from
# the model table. Role files set neither, so no role can run on a stale pin.
# Terra runs only at high effort. Noncoding model choices are not checked.
fail() {
  printf '%s\n' "$*" >&2
  exit 1
}
frontmatter() {
  awk -v key="$2" '
    NR == 1 && $0 == "---" { inside = 1; next }
    inside && $0 == "---" { exit }
    inside && index($0, key ": ") == 1 { print substr($0, length(key) + 3); exit }
  ' "$1"
}
check_role_model() {
  local file="$1" key
  test -s "$file" || fail "$file: missing role file."
  for key in model effort; do
    if [[ -n "$(frontmatter "$file" "$key")" ]]; then
      fail "$file: role files must not set '$key'. The orchestrator selects it."
    fi
  done
}
# Join wrapped lines so that "Terra" and its effort match across a line break.
check_terra_effort() {
  local file="$1"
  if tr '\n' ' ' < "$file" |
    grep -oiE 'terra( 6\.1)?[ ,]+(at |in |with )?`?(low|medium|xhigh|max)\b'; then
    fail "$file: Terra may run only at high effort."
  fi
  if grep -iE '^model = "[^"]*terra' -A1 "$file" | grep -E '^model_reasoning_effort = "(low|medium|xhigh|max)"'; then
    fail "$file: Terra may run only at high effort."
  fi
}
roles=(pr-builder pr-adversarial-reviewer pr-quick-reviewer pr-comment-analyzer pr-test-merger)
for role in "${roles[@]}"; do
  check_role_model "$root/claude/agents/$role.md"
done
for file in "$spec" "$command" "$root"/claude/agents/*.md; do
  check_terra_effort "$file"
done
# Every coding role in the model table uses Sonnet or Opus only.
if grep -nE '^\| (Small|Normal|Major) \|' "$spec" | grep -iE 'terra|haiku|astra|sol\b'; then
  fail 'The model table assigns a non-Sonnet, non-Opus model to a coding role.'
fi
if [[ $# -gt 0 ]]; then
  project="$1"
  for role in "${roles[@]}"; do
    check_role_model "$project/.claude/agents/$role.md"
  done
  for file in "$project"/.claude/agents/*.md "$project"/.codex/agents/*.toml; do
    test -f "$file" && check_terra_effort "$file"
  done
fi
# The diagram is generated. Fail when the committed SVG is stale.
svg="$root/docs/loomflow.svg"
before="$(cksum < "$svg")"
python3 "$root/scripts/generate-loomflow-diagram.py" > /dev/null
test "$before" = "$(cksum < "$svg")"
grep -Fq '(loomflow.svg)' "$spec"
"$root/scripts/check-install.sh"
if [[ $# -gt 0 ]]; then
  project="$1"
  grep -Fq 'breakbadsp/ai-assets/blob/main/docs/loomflow.md' "$project/docs/loomflow.md"
  grep -Fq '$HOME/ai/claude/commands/loomflow.md' "$project/.claude/commands/loomflow.md"
  for role in pr-builder pr-adversarial-reviewer pr-quick-reviewer pr-comment-analyzer pr-test-merger; do
    grep -Fq "\$HOME/ai/claude/agents/$role.md" "$project/.claude/agents/$role.md"
  done
fi
