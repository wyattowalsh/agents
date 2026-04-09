#!/bin/bash
command -v jq &>/dev/null || exit 0
INPUT=$(cat)
# CRITICAL: prevent infinite loop
[ "$(echo "$INPUT" | jq -r '.stop_hook_active // false')" = "true" ] && exit 0

CWD=$(echo "$INPUT" | jq -r '.cwd // empty')
[ -z "$CWD" ] && exit 0
cd "$CWD" 2>/dev/null || exit 0

ISSUES=""

if command -v git &>/dev/null && git rev-parse --git-dir &>/dev/null 2>&1; then
  MODIFIED=$(git diff --name-only 2>/dev/null; git diff --cached --name-only 2>/dev/null)
  if [ -n "$MODIFIED" ]; then
    # Check for debug artifacts (only in modified files, only dangerous patterns)
    DEBUG=$(echo "$MODIFIED" | while read -r f; do
      [ -f "$f" ] && grep -n 'debugger\|breakpoint()' "$f" 2>/dev/null | head -3
    done)
    [ -n "$DEBUG" ] && ISSUES="$(printf '%sDebug artifacts in modified files:\n%s\n\n' "$ISSUES" "$DEBUG")"

    # Python critical errors only (skip deleted files)
    PY=$(echo "$MODIFIED" | grep '\.py$' | while read -r f; do [ -f "$f" ] && echo "$f"; done)
    if [ -n "$PY" ] && [ -f "pyproject.toml" ] && command -v uv &>/dev/null; then
      ERRS=$(echo "$PY" | xargs uv run ruff check --select E9,F63,F7,F82 2>/dev/null | head -10)
      [ -n "$ERRS" ] && ISSUES="$(printf '%sPython errors:\n%s\n\n' "$ISSUES" "$ERRS")"
    elif [ -n "$PY" ] && command -v ruff &>/dev/null; then
      ERRS=$(echo "$PY" | xargs ruff check --select E9,F63,F7,F82 2>/dev/null | head -10)
      [ -n "$ERRS" ] && ISSUES="$(printf '%sPython errors:\n%s\n\n' "$ISSUES" "$ERRS")"
    fi
    TYPED_PY=$(echo "$PY" | grep -E '^(wagents|scripts)/')
    if [ -n "$TYPED_PY" ] && [ -f "pyproject.toml" ] && command -v uv &>/dev/null; then
      TY_ERRS=$(echo "$TYPED_PY" | xargs uv run --with ty==0.0.29 ty check --output-format concise --no-progress 2>&1)
      TY_EXIT=$?
      TY_ERRS=$(echo "$TY_ERRS" | head -10)
      [ $TY_EXIT -ne 0 ] && ISSUES="$(printf '%sPython type errors:\n%s\n\n' "$ISSUES" "$TY_ERRS")"
    fi

    # TypeScript errors
    if [ -f "tsconfig.json" ] && [ -f "node_modules/.bin/tsc" ]; then
      ERRS=$(timeout 30 node_modules/.bin/tsc --noEmit --pretty false 2>&1 | grep -v 'node_modules/' | grep -E 'error TS' | head -10)
      [ -n "$ERRS" ] && ISSUES="$(printf '%sTypeScript errors:\n%s\n\n' "$ISSUES" "$ERRS")"
    fi
  fi
fi

if [ -n "$ISSUES" ]; then
  jq -n --arg reason "$ISSUES" '{ decision: "block", reason: ("Issues detected before stopping:\n\n" + $reason) }'
  exit 0
fi
exit 0
