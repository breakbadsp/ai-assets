#!/usr/bin/env bash
# Usage: kaizen-checks.sh [--base REF] [--list | --all]
# Maps the changed files to the checks that they need, and runs only those.
# Run it locally and in CI: both read the same rules file, `.kaizen-checks`,
# in the repository root.
#
# Rules file: tab-separated lines. A `*` in a glob also matches `/`.
#   @all   <globs>                 a change here runs every check (blast radius)
#   <name> <globs> <command>       a change here runs this check
#   @skip  <globs>                 a change here needs no check
# A changed file that no rule names runs every check. This default is safe.
# Put dependents in the globs of a check: that is its blast radius.
# Changed files = merge-base with REF, the working tree, and untracked files.
set -euo pipefail

usage='usage: kaizen-checks.sh [--base REF] [--list | --all]'
base="" mode=run
while (($#)); do
  case "$1" in
    --base) base="${2:?$usage}"; shift 2 ;;
    --list) mode=list; shift ;;
    --all) mode=all; shift ;;
    *) printf '%s\n' "$usage" >&2; exit 2 ;;
  esac
done

cd "$(git rev-parse --show-toplevel)"
rules=.kaizen-checks
[[ -f "$rules" ]] || { printf 'Missing %s.\n' "$rules" >&2; exit 2; }

if [[ -z "$base" ]]; then
  base="$(git symbolic-ref -q --short refs/remotes/origin/HEAD || true)"
  base="${base:-main}"
fi
mb="$(git merge-base "$base" HEAD)" || { printf 'No merge base with %s. In CI, fetch full history.\n' "$base" >&2; exit 2; }

names=() globs=() cmds=() all_globs="" skip_globs=""
while IFS=$'\t' read -r name g cmd; do
  [[ -z "$name" || "$name" == '#'* ]] && continue
  case "$name" in
    @all) all_globs+=" $g" ;;
    @skip) skip_globs+=" $g" ;;
    *) names+=("$name"); globs+=("$g"); cmds+=("$cmd") ;;
  esac
done <"$rules"

matches() { # file, space-separated globs
  local pattern
  set -f
  for pattern in $2; do
    # shellcheck disable=SC2053
    if [[ "$1" == $pattern ]]; then set +f; return 0; fi
  done
  set +f
  return 1
}

declare -A need=()
run_all=0
if [[ "$mode" == all ]]; then
  run_all=1
else
  while IFS= read -r file; do
    [[ -z "$file" ]] && continue
    if matches "$file" "$all_globs"; then
      printf 'all: %s is shared\n' "$file" >&2; run_all=1; break
    fi
    hit=0
    for i in "${!names[@]}"; do
      if matches "$file" "${globs[$i]}"; then need[$i]=1; hit=1; fi
    done
    ((hit)) && continue
    matches "$file" "$skip_globs" && continue
    printf 'all: no rule names %s\n' "$file" >&2; run_all=1; break
  done < <({ git diff --name-only --no-renames "$mb"; git ls-files -o --exclude-standard; } | sort -u)
fi
if ((run_all)); then
  for i in "${!names[@]}"; do need[$i]=1; done
fi

selected=()
for i in "${!names[@]}"; do [[ -n "${need[$i]:-}" ]] && selected+=("$i"); done
if ((${#selected[@]} == 0)); then
  printf 'No checks needed.\n'
  exit 0
fi

if [[ "$mode" == list ]]; then
  for i in "${selected[@]}"; do printf '%s\n' "${names[$i]}"; done
  exit 0
fi

failed=()
for i in "${selected[@]}"; do
  printf '== %s: %s\n' "${names[$i]}" "${cmds[$i]}"
  bash -c "${cmds[$i]}" || failed+=("${names[$i]}")
done
printf 'Ran %d of %d checks.\n' "${#selected[@]}" "${#names[@]}"
if ((${#failed[@]})); then
  printf 'Failed: %s\n' "${failed[*]}" >&2
  exit 1
fi
