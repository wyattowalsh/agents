#!/bin/bash
command -v jq &>/dev/null || exit 0
INPUT=$(cat)
PROMPT=$(echo "$INPUT" | jq -r '.prompt // empty')
TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
LOG_DIR="$HOME/.claude/logs"
mkdir -p "$LOG_DIR" && chmod 700 "$LOG_DIR"
printf '%s' "$PROMPT" | jq -Rs --arg ts "$TS" '{ts: $ts, prompt: .}' >> "${LOG_DIR}/prompts-$(date +%Y-%m-%d).jsonl"
# Clean up logs older than 30 days
find "$LOG_DIR" -name "prompts-*.jsonl" -mtime +30 -delete 2>/dev/null
exit 0
