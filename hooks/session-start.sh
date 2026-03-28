#!/bin/bash
ERRORS=""
for tool in jq git uv node; do
  command -v "$tool" &>/dev/null || ERRORS="${ERRORS}WARNING: '${tool}' not found"$'\n'
done

if [ -n "$CLAUDE_ENV_FILE" ]; then
  echo 'export PYTHONDONTWRITEBYTECODE=1' >> "$CLAUDE_ENV_FILE"
fi

if command -v git &>/dev/null && git rev-parse --git-dir &>/dev/null 2>&1; then
  BRANCH=$(git branch --show-current 2>/dev/null)
  echo "Branch: ${BRANCH}"
  DIRTY=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
  [ "$DIRTY" -gt 0 ] && echo "Uncommitted changes: ${DIRTY} files"
fi

[ -n "$ERRORS" ] && printf "%s" "$ERRORS"
echo "Success"
exit 0
