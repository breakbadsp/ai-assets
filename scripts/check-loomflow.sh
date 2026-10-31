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
done
grep -Fq 'GPT 6.1 Terra' "$spec"
! grep -q 'Haiku' "$spec" "$command"
# Keep role defaults and fallback instructions within the reasoning policy.
grep -Fq 'Never use reasoning effort above high' "$root/AGENTS.md"
grep -Fq 'Always use Opus at medium effort' "$root/AGENTS.md"
grep -Fxq 'effort: medium' "$root/claude/agents/pr-builder.md"
if grep -En 'Opus 5\.5[, ]+`?high|Sol `?xhigh|effort: (xhigh|max|ultra)' \
  "$root/AGENTS.md" "$spec" "$command" "$root"/claude/agents/*.md; then
  printf 'Reasoning settings exceed the policy.\n' >&2
  exit 1
fi
"$root/scripts/check-install.sh"
if [[ $# -gt 0 ]]; then
  project="$1"
  grep -Fq 'breakbadsp/ai-assets/blob/main/docs/loomflow.md' "$project/docs/loomflow.md"
  grep -Fq '$HOME/ai/claude/commands/loomflow.md' "$project/.claude/commands/loomflow.md"
  for role in pr-builder pr-adversarial-reviewer pr-quick-reviewer pr-comment-analyzer pr-test-merger; do
    grep -Fq "\$HOME/ai/claude/agents/$role.md" "$project/.claude/agents/$role.md"
  done
fi
