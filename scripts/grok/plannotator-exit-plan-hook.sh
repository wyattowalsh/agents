#!/usr/bin/env bash
# Grok PreToolUse wrapper for Plannotator plan review (delegates to Python shim).
# The Python shim resolves session plan.md, adapts Claude-shaped stdin for
# plannotator, and maps allow/deny/block decisions to Grok native JSON.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "${SCRIPT_DIR}/plannotator-exit-plan-hook.py"