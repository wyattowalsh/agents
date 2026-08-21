#!/usr/bin/env bash
# Fail-open Atuin agent history hook. Missing Atuin or a hook error must not
# block Claude Code / Codex Bash tool use. stdin is the harness event JSON.
PATH="/opt/homebrew/bin:/usr/local/bin:${HOME}/.local/bin:${PATH:-/usr/bin:/bin}"
export PATH

agent="${1:-}"
if [ -z "$agent" ]; then
  exit 0
fi
if ! command -v atuin >/dev/null 2>&1; then
  exit 0
fi
atuin hook "$agent" || true
exit 0
