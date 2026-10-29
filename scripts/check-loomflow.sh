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
if [[ $# -gt 0 ]]; then
  project="$1"
  grep -Fq 'breakbadsp/ai-assets/blob/main/docs/loomflow.md' "$project/docs/loomflow.md"
  grep -Fq '$HOME/ai/claude/commands/loomflow.md' "$project/.claude/commands/loomflow.md"
  for role in pr-builder pr-adversarial-reviewer pr-quick-reviewer pr-comment-analyzer pr-test-merger; do
    grep -Fq "\$HOME/ai/claude/agents/$role.md" "$project/.claude/agents/$role.md"
  done
fi
