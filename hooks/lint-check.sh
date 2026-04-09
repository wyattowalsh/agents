#!/bin/bash
command -v jq &>/dev/null || exit 0
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '
  .tool_input.file_path
  // (
    (.toolArgs | fromjson? // .toolArgs // {})
    | if type == "object" then (.filePath // .path // .target_file // empty) else empty end
  )
  // empty
')
[ -z "$FILE_PATH" ] || [ ! -f "$FILE_PATH" ] && exit 0

case "${FILE_PATH##*.}" in
  py)
    DETAILS=""
    if [ -f "pyproject.toml" ] && command -v uv &>/dev/null; then
      LINT=$(uv run ruff check "$FILE_PATH" 2>&1)
      LINT_EXIT=$?
      LINT=$(echo "$LINT" | head -20)
      [ $LINT_EXIT -ne 0 ] && printf -v DETAILS "%sRuff issues in %s:\n%s\n\n" "$DETAILS" "$FILE_PATH" "$LINT"
    elif command -v ruff &>/dev/null; then
      LINT=$(ruff check "$FILE_PATH" 2>&1)
      LINT_EXIT=$?
      LINT=$(echo "$LINT" | head -20)
      [ $LINT_EXIT -ne 0 ] && printf -v DETAILS "%sRuff issues in %s:\n%s\n\n" "$DETAILS" "$FILE_PATH" "$LINT"
    fi
    if [ -f "pyproject.toml" ] && command -v uv &>/dev/null; then
      case "$FILE_PATH" in
        wagents/*|scripts/*)
          TYPECHECK=$(uv run ty check --output-format concise --no-progress "$FILE_PATH" 2>&1)
          TYPECHECK_EXIT=$?
          TYPECHECK=$(echo "$TYPECHECK" | head -20)
          [ $TYPECHECK_EXIT -ne 0 ] && printf -v DETAILS "%sTy issues in %s:\n%s\n" "$DETAILS" "$FILE_PATH" "$TYPECHECK"
          ;;
      esac
    fi
    [ -n "$DETAILS" ] && jq -n --arg msg "$DETAILS" '{"hookSpecificOutput":{"hookEventName":"PostToolUse"},"additionalContext":$msg}' ;;
  ts|tsx)
    if [ -f "node_modules/.bin/tsc" ]; then
      ERRS=$(timeout 25 node_modules/.bin/tsc --noEmit --pretty false 2>&1)
      TSC_EXIT=$?
      ERRS=$(echo "$ERRS" | head -20)
      [ $TSC_EXIT -ne 0 ] && printf -v MSG "TypeScript errors:\n%s" "$ERRS" && \
        jq -n --arg msg "$MSG" '{"hookSpecificOutput":{"hookEventName":"PostToolUse"},"additionalContext":$msg}'
    fi ;;
esac
exit 0
