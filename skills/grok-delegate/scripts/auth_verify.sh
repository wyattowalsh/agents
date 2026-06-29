#!/usr/bin/env bash
# Deep Grok auth smoke: bounded grok -p ping (optional; requires interactive OAuth refresh).
set -euo pipefail

CWD=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --cwd)
      CWD="${2:-}"
      shift 2
      ;;
    *)
      echo "Usage: auth_verify.sh --cwd <absolute-repo-path>" >&2
      exit 2
      ;;
  esac
done

if [[ -z "${CWD}" ]]; then
  echo "auth_verify.sh requires --cwd" >&2
  exit 2
fi

if ! command -v grok >/dev/null 2>&1; then
  echo '{"ok":false,"error":"grok binary not found"}' >&2
  exit 1
fi

if command -v timeout >/dev/null 2>&1; then
  TIMEOUT_CMD=(timeout 20)
elif command -v gtimeout >/dev/null 2>&1; then
  TIMEOUT_CMD=(gtimeout 20)
else
  TIMEOUT_CMD=()
fi

STDERR_FILE="$(mktemp)"
trap 'rm -f "${STDERR_FILE}"' EXIT

OUTPUT="$("${TIMEOUT_CMD[@]}" grok --no-auto-update \
  -p 'Reply with exactly: pong' \
  --cwd "${CWD}" \
  --output-format json \
  --max-turns 1 2>"${STDERR_FILE}" || true)"
STDERR_CONTENT="$(cat "${STDERR_FILE}")"

emit_failure() {
  export GROK_AUTH_VERIFY_ERROR="$1"
  export GROK_AUTH_VERIFY_STDERR="${STDERR_CONTENT}"
  export GROK_AUTH_VERIFY_RAW="${2:-}"
  python3 - <<'PY' >&2
import json
import os
import re

def redact_stderr(text: str) -> str:
    patterns = [
        r"(?i)(bearer\s+)\S+",
        r"(?i)(refresh_token|access_token|api[_-]?key|xai[_-]?api[_-]?key)\s*[:=]\s*\S+",
    ]
    redacted = text
    for pattern in patterns:
        redacted = re.sub(pattern, r"\1[REDACTED]", redacted)
    return redacted[:500]

payload = {
    "ok": False,
    "error": os.environ["GROK_AUTH_VERIFY_ERROR"],
}
stderr = os.environ.get("GROK_AUTH_VERIFY_STDERR", "")
if stderr:
    payload["stderr"] = redact_stderr(stderr)
raw = os.environ.get("GROK_AUTH_VERIFY_RAW", "")
if raw:
    payload["raw"] = raw
print(json.dumps(payload))
PY
}

if [[ -z "${OUTPUT}" ]]; then
  emit_failure "grok -p smoke timed out or produced no output"
  exit 1
fi

if echo "${OUTPUT}" | grep -qi pong; then
  echo '{"ok":true,"summary":"grok -p auth smoke succeeded"}'
  exit 0
fi

emit_failure "unexpected grok -p output" "${OUTPUT}"
exit 1