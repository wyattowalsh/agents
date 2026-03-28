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

COMMAND=$(echo "$INPUT" | jq -r '
  .tool_input.command
  // (
    (.toolArgs | fromjson? // .toolArgs // {})
    | if type == "object" then (.command // .cmd // empty) else empty end
  )
  // empty
')
[ -z "$COMMAND" ] && exit 0

# Block rm -rf on critical paths (but allow rm -rf ./build, ./node_modules, etc.)
if echo "$COMMAND" | grep -qE '(sudo\s+)?rm\s+(-[a-zA-Z]*r[a-zA-Z]*f|--recursive\s+--force|-[a-zA-Z]*f[a-zA-Z]*r)\s+(/|~|\$HOME|/Users|/System|/Library|/etc|/var|/usr|\.\.|\./?$)'; then
  emit_pretool_deny "rm -rf on critical system path. Use a more specific path."
  exit 0
fi

# Block piping remote scripts to shell
if echo "$COMMAND" | grep -qE 'curl\s+.*\|\s*(ba)?sh|wget\s+.*\|\s*(ba)?sh'; then
  emit_pretool_deny "Piping remote script to shell. Download and review first."
  exit 0
fi

# Block force push to main/master (but allow --force-with-lease)
if echo "$COMMAND" | grep -qE 'git\s+push\b' && \
   echo "$COMMAND" | grep -qE '\s(--force(\s|$)|-f(\s|$))' && \
   echo "$COMMAND" | grep -qE '\s(main|master)(\s|$)' && \
   ! echo "$COMMAND" | grep -qE '--force-with-lease'; then
  emit_pretool_deny "Force push to main/master. Use --force-with-lease instead."
  exit 0
fi

# Block git reset --hard (can destroy uncommitted work)
if echo "$COMMAND" | grep -qE 'git\s+reset\s+--hard'; then
  emit_pretool_deny "git reset --hard can destroy uncommitted work. Stash or commit first."
  exit 0
fi

# Block git clean -f (permanently removes untracked files)
if echo "$COMMAND" | grep -qE 'git\s+clean\s+-[a-zA-Z]*f'; then
  emit_pretool_deny "git clean -f permanently removes untracked files."
  exit 0
fi
exit 0
