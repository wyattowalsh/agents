#!/bin/bash
# Run post-edit format and lint checks concurrently for Copilot bundle tier.
set -euo pipefail

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
INPUT=$(cat)

format_out=$(mktemp)
lint_out=$(mktemp)
trap 'rm -f "$format_out" "$lint_out"' EXIT

printf '%s' "$INPUT" | bash "$script_dir/auto-format.sh" >"$format_out" 2>/dev/null &
format_pid=$!
printf '%s' "$INPUT" | bash "$script_dir/lint-check.sh" >"$lint_out" 2>/dev/null &
lint_pid=$!

wait "$format_pid" || true
wait "$lint_pid" || true

if [ -s "$lint_out" ]; then
  cat "$lint_out"
fi

exit 0
