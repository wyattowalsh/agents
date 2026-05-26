#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

mcphub_load_env
mcphub_require_token
"${SCRIPT_DIR}/ensure-running.sh"

curl -fsS "$(mcphub_health_url)" >/dev/null

headers_file="$(mktemp)"
trap 'rm -f "${headers_file}"' EXIT

curl -fsS \
  -D "${headers_file}" \
  -H "Authorization: Bearer ${MCPHUB_BEARER_TOKEN}" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"mcphub-smoke","version":"1.0.0"}}}' \
  "${MCPHUB_BASE_URL%/}/mcp" >/dev/null

session_id="$(
  awk 'BEGIN{IGNORECASE=1} /^mcp-session-id:/ {sub(/\r$/, "", $2); print $2; exit}' "${headers_file}"
)"
if [[ -z "${session_id}" ]]; then
  printf 'MCPHub smoke failed: initialize response did not include mcp-session-id\n' >&2
  exit 1
fi

curl -fsS \
  -H "Authorization: Bearer ${MCPHUB_BEARER_TOKEN}" \
  -H "Mcp-Session-Id: ${session_id}" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' \
  "${MCPHUB_BASE_URL%/}/mcp" >/dev/null

printf 'MCPHub smoke passed\n'
