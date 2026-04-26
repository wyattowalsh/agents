#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${AGENTS_REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
MCP_ROOT="${AGENTS_MCP_ROOT:-$REPO_ROOT/mcp}"
APPLY=0
INCLUDE_DEPS=0

usage() {
  cat <<EOF
Usage: $0 [--dry-run] [--apply] [--include-deps]

Default is --dry-run. This script removes generated cache artifacts only.
--include-deps also includes node_modules, .venv, and venv directories.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) APPLY=0 ;;
    --apply) APPLY=1 ;;
    --include-deps) INCLUDE_DEPS=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

if [[ ! -d "$MCP_ROOT" ]]; then
  echo "MCP root does not exist: $MCP_ROOT" >&2
  exit 1
fi

if [[ "$INCLUDE_DEPS" -eq 1 ]]; then
  mapfile -d '' candidates < <(
    find "$MCP_ROOT" \
      \( -name .DS_Store -o -name __pycache__ -o -name .pytest_cache -o -name .mypy_cache -o -name .ruff_cache -o -name '*.pyc' -o -name '*.pyo' -o -name '*.log' -o -name '*.pid' \) \
      -print0
  )
else
  mapfile -d '' candidates < <(
    find "$MCP_ROOT" \
      \( -name node_modules -o -name .venv -o -name venv \) -type d -prune -o \
      \( -name .DS_Store -o -name __pycache__ -o -name .pytest_cache -o -name .mypy_cache -o -name .ruff_cache -o -name '*.pyc' -o -name '*.pyo' -o -name '*.log' -o -name '*.pid' \) \
      -print0
  )
fi

if [[ "$INCLUDE_DEPS" -eq 1 ]]; then
  while IFS= read -r -d '' dep; do
    candidates+=("$dep")
  done < <(find "$MCP_ROOT/servers" \( -name node_modules -o -name .venv -o -name venv \) -type d -prune -print0 2>/dev/null || true)
fi

if [[ "${#candidates[@]}" -eq 0 ]]; then
  echo "No cleanup candidates found under $MCP_ROOT"
  exit 0
fi

if [[ "$APPLY" -eq 0 ]]; then
  echo "Dry run: would remove ${#candidates[@]} generated/cache artifact(s):"
  printf '%s\n' "${candidates[@]}"
  exit 0
fi

for candidate in "${candidates[@]}"; do
  rm -rf "$candidate"
done
echo "Removed ${#candidates[@]} generated/cache artifact(s)."
