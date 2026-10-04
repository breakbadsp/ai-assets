#!/usr/bin/env bash
set -euo pipefail

asset_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
if [[ "$asset_root" != "$HOME/ai" ]]; then
  printf 'Install this repository at %s/ai first.\n' "$HOME" >&2
  exit 1
fi

sources=("$asset_root/AGENTS.md" "$asset_root/workspace/AGENTS.md" "$asset_root/conventions/cpp.md")
targets=("$HOME/.codex/AGENTS.md" "$HOME/AGENTS.md" "$HOME/.codex/conventions/cpp.md")

# Check every target before changing any links.
for i in "${!targets[@]}"; do
  target="${targets[$i]}"
  if [[ -e "$target" || -L "$target" ]]; then
    if [[ ! -L "$target" ]] || [[ "$(readlink -- "$target")" != "${sources[$i]}" ]]; then
      printf 'Refusing to replace existing path: %s\n' "$target" >&2
      exit 1
    fi
  fi
done

for i in "${!targets[@]}"; do
  target="${targets[$i]}"
  mkdir -p -- "$(dirname -- "$target")"
  if [[ ! -L "$target" ]]; then
    ln -s -- "${sources[$i]}" "$target"
  fi
  printf '%s -> %s\n' "$target" "${sources[$i]}"
done
