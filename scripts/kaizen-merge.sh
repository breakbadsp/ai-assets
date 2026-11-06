#!/usr/bin/env bash
# Usage: kaizen-merge.sh <PR> <head SHA> [--no-ci]
# Waits for CI, then merges exactly <head SHA>. Run it from the PR repository.
#
# A plain `gh pr checks --watch && gh pr merge` is not safe: `gh pr checks`
# exits 0 when a check is cancelled, and a branch may have no protection.
set -euo pipefail

usage='usage: kaizen-merge.sh <PR> <head SHA> [--no-ci]'
pr="${1:?$usage}"
sha="${2:?$usage}"
no_ci="${3:-}"
if [[ -n "$no_ci" && "$no_ci" != --no-ci ]]; then
  printf '%s\n' "$usage" >&2
  exit 2
fi

if [[ -z "$no_ci" ]]; then
  # New checks need a short time to register after a push.
  for attempt in 1 2 3 4 5 6; do
    if [[ "$(gh pr checks "$pr" 2>&1)" != *'no checks reported'* ]]; then
      break
    fi
    if [[ "$attempt" == 6 ]]; then
      printf 'Not merged: no checks reported on PR %s.\n' "$pr" >&2
      exit 1
    fi
    sleep 10
  done
  if ! timeout 2700 gh pr checks "$pr" --watch --fail-fast >/dev/null; then
    printf 'Not merged: a check failed or the wait timed out.\n' >&2
    gh pr checks "$pr" | grep -v 'pass' >&2 || true
    exit 1
  fi
  # Each check must end as pass or skipping. This rejects cancelled checks.
  bad="$(gh pr checks "$pr" --json name,bucket \
    -q '.[] | select(.bucket != "pass" and .bucket != "skipping") | "\(.bucket)\t\(.name)"')"
  if [[ -n "$bad" ]]; then
    printf 'Not merged: these checks did not pass:\n%s\n' "$bad" >&2
    exit 1
  fi
fi

gh pr merge "$pr" --merge --match-head-commit "$sha"
printf 'Merged PR %s at head %s.\n' "$pr" "$sha"
