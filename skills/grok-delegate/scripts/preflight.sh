#!/usr/bin/env bash
# Grok delegate preflight: prefer repo wagents doctor when available.
set -euo pipefail

if command -v uv >/dev/null 2>&1 && { [ -f pyproject.toml ] || [ -f uv.lock ]; }; then
  uv run wagents grok doctor --format json
  exit $?
fi

if command -v wagents >/dev/null 2>&1; then
  wagents grok doctor --format json
  exit $?
fi

echo '{"ok":false,"summary":{"fail":1},"checks":[{"name":"grok-binary","status":"fail","summary":"grok or wagents doctor unavailable"}]}' >&2
exit 1