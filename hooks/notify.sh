#!/bin/bash
TYPE="${1:-generic}"

# Graceful degradation: skip on non-macOS or headless
[ "$(uname)" != "Darwin" ] && exit 0
pgrep -x "WindowServer" > /dev/null 2>&1 || exit 0

INPUT=$(cat)
MSG=$(echo "$INPUT" | jq -r '.message // "Claude Code needs attention"' 2>/dev/null)

NOTIFIER="/opt/homebrew/bin/terminal-notifier"
[ ! -x "$NOTIFIER" ] && NOTIFIER="$(command -v terminal-notifier 2>/dev/null)"
[ -z "$NOTIFIER" ] && exit 0

SOUND="$HOME/Library/Sounds/GhosttyNotify.aiff"
[ -f "$SOUND" ] && afplay "$SOUND" &>/dev/null &

case "$TYPE" in
  permission)
    "$NOTIFIER" -title "Claude Code" -subtitle "Permission Required" \
      -message "$MSG" -sound "GhosttyNotify" \
      -sender com.mitchellh.ghostty >/dev/null 2>&1
    ;;
  idle)
    "$NOTIFIER" -title "Claude Code" -subtitle "Waiting" \
      -message "$MSG" -sound "GhosttyNotify" \
      -sender com.mitchellh.ghostty >/dev/null 2>&1
    ;;
  *)
    "$NOTIFIER" -title "Claude Code" \
      -message "$MSG" -sound "GhosttyNotify" \
      -sender com.mitchellh.ghostty >/dev/null 2>&1
    ;;
esac
exit 0
