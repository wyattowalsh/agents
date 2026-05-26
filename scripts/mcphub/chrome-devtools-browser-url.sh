#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

mcphub_load_env

CHROME_BIN="${CHROME_DEVTOOLS_MCP_CHROME_BIN:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
PROFILE_DIR="${CHROME_DEVTOOLS_MCP_PROFILE_DIR:-/Users/ww/.cache/chrome-devtools-mcp-login}"
DEBUG_HOST="${CHROME_DEVTOOLS_MCP_DEBUG_HOST:-127.0.0.1}"
DEBUG_PORT="${CHROME_DEVTOOLS_MCP_DEBUG_PORT:-9333}"
DEBUG_URL="http://${DEBUG_HOST}:${DEBUG_PORT}"

devtools_ready() {
  python3 - <<PY
import json
import urllib.request

try:
    with urllib.request.urlopen("${DEBUG_URL}/json/version", timeout=0.5) as response:
        payload = json.load(response)
except Exception:
    raise SystemExit(1)
if payload.get("Browser") and payload.get("webSocketDebuggerUrl"):
    raise SystemExit(0)
raise SystemExit(1)
PY
}

if [[ ! -x "${CHROME_BIN}" ]]; then
  printf 'Chrome binary not found at %s\n' "${CHROME_BIN}" >&2
  exit 1
fi

mkdir -p "${PROFILE_DIR}"

if ! devtools_ready; then
  "${CHROME_BIN}" \
    --remote-debugging-address="${DEBUG_HOST}" \
    --remote-debugging-port="${DEBUG_PORT}" \
    --user-data-dir="${PROFILE_DIR}" \
    --no-first-run \
    --no-default-browser-check \
    >/dev/null 2>&1 &

  for _ in {1..50}; do
    if devtools_ready; then
      break
    fi
    sleep 0.2
  done
fi

if ! devtools_ready; then
  printf 'Chrome DevTools endpoint did not become ready at %s\n' "${DEBUG_URL}" >&2
  exit 1
fi

exec npx -y chrome-devtools-mcp@latest \
  --browserUrl "${DEBUG_URL}" \
  --no-usage-statistics \
  --no-performance-crux \
  "$@"
