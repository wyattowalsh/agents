#!/usr/bin/env bash
set -euo pipefail

command -v jq >/dev/null 2>&1 || exit 0
INPUT=$(cat)
is_copilot_payload() {
  echo "$INPUT" | jq -e 'has("toolName") and has("toolArgs")' >/dev/null 2>&1
}

emit_pretool_deny() {
  local reason="$1"
  if is_copilot_payload; then
    jq -cn --arg reason "$reason" '{permissionDecision:"deny", permissionDecisionReason:$reason}'
  else
    jq -cn --arg reason "$reason" '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":$reason}}'
  fi
}

FILE_PATH=$(echo "$INPUT" | jq -r '
  .tool_input.file_path
  // (
    (.toolArgs | fromjson? // .toolArgs // {})
    | if type == "object" then (.filePath // .path // .target_file // empty) else empty end
  )
  // empty
')
[ -z "$FILE_PATH" ] && exit 0

# Block path traversal
echo "$FILE_PATH" | grep -qE '\.\.(\/|$)' && {
  emit_pretool_deny "Path traversal detected."
  exit 0
}

# Protected files — match on basename to avoid false positives (e.g., .envrc, config.env.example)
BASENAME=$(basename "$FILE_PATH")
for pattern in ".env" ".env.local" ".env.production" ".env.staging" ".env.development" ".env.test" "credentials.json" "token.pickle"; do
  if [[ "$BASENAME" == "$pattern" ]]; then
    emit_pretool_deny "Protected file: $FILE_PATH"
    exit 0
  fi
done

# Protected paths — suffix match (no trailing *) to avoid blocking .pub files
for pattern in "/.ssh/id_rsa" "/.ssh/id_ed25519" "/.git/config" "/.git/HEAD"; do
  if [[ "$FILE_PATH" == *"$pattern" ]]; then
    emit_pretool_deny "Protected path: $FILE_PATH"
    exit 0
  fi
done

# Deny lock file edits
if echo "$FILE_PATH" | grep -qE '\.(lock|lockb)$|lock\.json$|lock\.yaml$'; then
  emit_pretool_deny "Lock files should not be edited directly. Use the package manager instead."
  exit 0
fi
exit 0
