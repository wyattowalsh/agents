#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

readonly CURL_CONNECT_TIMEOUT_SECONDS=5
readonly CURL_MAX_TIME_SECONDS=120
readonly MCP_INITIALIZE_ID=1
readonly MCP_TOOLS_LIST_ID=2
readonly MCP_PROTOCOL_VERSION=2025-11-25

for required_command in curl uv; do
  if ! command -v "${required_command}" >/dev/null 2>&1; then
    printf 'MCPHub smoke failed: required command is unavailable: %s\n' "${required_command}" >&2
    exit 1
  fi
done

mcphub_load_env
mcphub_require_token
"${SCRIPT_DIR}/ensure-running.sh"
if ! mcphub_local_route_is_ready; then
  printf 'MCPHub smoke failed: authenticated exact-route readiness did not pass\n' >&2
  exit 1
fi

readonly ENDPOINT="${MCPHUB_BASE_URL}/mcp/things"
readonly -a CURL_ARGS=(
  --fail
  --silent
  --show-error
  --connect-timeout "${CURL_CONNECT_TIMEOUT_SECONDS}"
  --max-time "${CURL_MAX_TIME_SECONDS}"
)

temp_dir="$(mktemp -d)"
trap 'rm -rf "${temp_dir}"' EXIT

initialize_headers="${temp_dir}/initialize.headers"
initialize_body="${temp_dir}/initialize.body"
tools_headers="${temp_dir}/tools.headers"
tools_body="${temp_dir}/tools.body"

curl "${CURL_ARGS[@]}" \
  -D "${initialize_headers}" \
  -o "${initialize_body}" \
  -H "Authorization: Bearer ${MCPHUB_BEARER_TOKEN}" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "MCP-Protocol-Version: ${MCP_PROTOCOL_VERSION}" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"mcphub-things-smoke","version":"1.0.0"}}}' \
  "${ENDPOINT}"

protocol_version="$(
  uv run python "${SCRIPT_DIR}/mcp_response.py" protocol-version \
    --headers "${initialize_headers}" \
    --body "${initialize_body}" \
    --response-id "${MCP_INITIALIZE_ID}"
)"
if [[ "${protocol_version}" != "${MCP_PROTOCOL_VERSION}" ]]; then
  printf 'MCPHub smoke failed: initialize negotiated unexpected protocol %s\n' "${protocol_version}" >&2
  exit 1
fi

curl "${CURL_ARGS[@]}" \
  -D "${tools_headers}" \
  -o "${tools_body}" \
  -H "Authorization: Bearer ${MCPHUB_BEARER_TOKEN}" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "MCP-Protocol-Version: ${MCP_PROTOCOL_VERSION}" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' \
  "${ENDPOINT}"

uv run python - \
  "${SCRIPT_DIR}" \
  "${initialize_headers}" \
  "${tools_headers}" \
  "${tools_body}" \
  "${MCPHUB_SETTING_PATH}" \
  "${MCP_TOOLS_LIST_ID}" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

script_dir, initialize_headers, tools_headers, tools_body, settings_path, response_id = sys.argv[1:]
sys.path.insert(0, script_dir)
from mcp_response import parse_final_headers, parse_tool_names  # noqa: E402

for header_path in (initialize_headers, tools_headers):
    headers = parse_final_headers(Path(header_path).read_bytes())
    if "mcp-session-id" in headers:
        raise SystemExit("MCPHub smoke failed: legacy stateless response created a session")

names = parse_tool_names(
    Path(tools_headers).read_bytes(),
    Path(tools_body).read_bytes(),
    response_id=int(response_id),
)
settings = json.loads(Path(settings_path).read_text(encoding="utf-8"))
contract = settings.get("thingsContract")
if not isinstance(contract, dict):
    raise SystemExit("MCPHub smoke failed: runtime settings omit thingsContract")
rows = contract.get("tools")
if not isinstance(rows, list):
    raise SystemExit("MCPHub smoke failed: thingsContract.tools is not a list")
expected = [row.get("publicToolName") for row in rows if isinstance(row, dict)]
if len(expected) != 70 or len(set(expected)) != 70 or set(names) != set(expected):
    raise SystemExit("MCPHub smoke failed: tools/list is not the exact 70-tool contract")
PY

printf 'MCPHub smoke passed (authenticated /mcp/things; legacy stateless; exact 70-tool contract)\n'
