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
    command -v ruff &>/dev/null && ruff format "$FILE_PATH" 2>/dev/null ;;
  js|jsx|ts|tsx|css|scss|html|json|yaml|yml)
    if [ -f "node_modules/.bin/prettier" ]; then
      node_modules/.bin/prettier --write "$FILE_PATH" 2>/dev/null
    elif command -v prettier &>/dev/null; then
      prettier --write "$FILE_PATH" 2>/dev/null
    fi ;;
  rs) command -v rustfmt &>/dev/null && rustfmt "$FILE_PATH" 2>/dev/null ;;
  go) command -v gofmt &>/dev/null && gofmt -w "$FILE_PATH" 2>/dev/null ;;
esac
exit 0
