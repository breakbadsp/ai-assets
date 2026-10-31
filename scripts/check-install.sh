#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf -- "$tmp"' EXIT
# The installer needs the repository at $HOME/ai, so use a copy and a clean home.
mkdir -p "$tmp/ai"
tar -C "$root" --exclude=.git -cf - . | tar -C "$tmp/ai" -xf -
export HOME="$tmp"
"$tmp/ai/install.sh" >/dev/null
count=0
for source in "$tmp"/ai/claude/commands/*.md "$tmp"/ai/claude/agents/*.md; do
  target="$HOME/.claude/${source#"$tmp"/ai/claude/}"
  test -L "$target"
  test "$(readlink -- "$target")" = "$source"
  count=$((count + 1))
done
test "$count" -gt 0
# A second run must succeed and keep the same links.
"$tmp/ai/install.sh" >/dev/null
test "$(readlink -- "$HOME/.claude/commands/loomflow.md")" = "$tmp/ai/claude/commands/loomflow.md"
printf 'Installer check passed: %s Claude links.\n' "$count"
