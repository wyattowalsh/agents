#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/mcphub/common.sh
source "${SCRIPT_DIR}/common.sh"

readonly CURL_CONNECT_TIMEOUT_SECONDS=5
readonly CURL_MAX_TIME_SECONDS=120
readonly MCP_INITIALIZE_ID=1
readonly MCP_TOOLS_LIST_ID=2
readonly -a DDGS_EXPECTED_TOOLS=(
  "ddgs-extract_content"
  "ddgs-search_books"
  "ddgs-search_images"
  "ddgs-search_news"
  "ddgs-search_text"
  "ddgs-search_videos"
)

for required_command in curl uv; do
  if ! command -v "${required_command}" >/dev/null 2>&1; then
    printf 'MCPHub smoke failed: required command is unavailable: %s\n' "${required_command}" >&2
    exit 1
  fi
done

mcphub_load_env
mcphub_require_token
"${SCRIPT_DIR}/ensure-running.sh"

readonly -a CURL_ARGS=(
  --fail
  --silent
  --show-error
  --connect-timeout "${CURL_CONNECT_TIMEOUT_SECONDS}"
  --max-time "${CURL_MAX_TIME_SECONDS}"
)

temp_dir="$(mktemp -d)"
trap 'rm -rf "${temp_dir}"' EXIT

curl "${CURL_ARGS[@]}" "$(mcphub_health_url)" >/dev/null

smoke_endpoint() {
  local endpoint_url="$1"
  local endpoint_label="$2"
  local assertion_mode="$3"
  shift 3
  local -a expected_tools=("$@")
  local initialize_headers="${temp_dir}/${endpoint_label}-initialize.headers"
  local initialize_body="${temp_dir}/${endpoint_label}-initialize.body"
  local tools_headers="${temp_dir}/${endpoint_label}-tools.headers"
  local tools_body="${temp_dir}/${endpoint_label}-tools.body"
  local session_id protocol_version notification_status

  curl "${CURL_ARGS[@]}" \
    -D "${initialize_headers}" \
    -o "${initialize_body}" \
    -H "Authorization: Bearer ${MCPHUB_BEARER_TOKEN}" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"mcphub-smoke","version":"1.0.0"}}}' \
    "${endpoint_url}"

  session_id="$(
    uv run python "${SCRIPT_DIR}/mcp_response.py" session-id \
      --headers "${initialize_headers}"
  )"
  protocol_version="$(
    uv run python "${SCRIPT_DIR}/mcp_response.py" protocol-version \
      --headers "${initialize_headers}" \
      --body "${initialize_body}" \
      --response-id "${MCP_INITIALIZE_ID}"
  )"

  notification_status="$(
    curl "${CURL_ARGS[@]}" \
      -o /dev/null \
      --write-out '%{http_code}' \
      -H "Authorization: Bearer ${MCPHUB_BEARER_TOKEN}" \
      -H "Mcp-Session-Id: ${session_id}" \
      -H "MCP-Protocol-Version: ${protocol_version}" \
      -H "Content-Type: application/json" \
      -H "Accept: application/json, text/event-stream" \
      -d '{"jsonrpc":"2.0","method":"notifications/initialized","params":{}}' \
      "${endpoint_url}"
  )"
  if [[ "${notification_status}" != "202" ]]; then
    printf 'MCPHub smoke failed: %s initialized notification returned HTTP %s, expected 202\n' \
      "${endpoint_label}" "${notification_status}" >&2
    return 1
  fi

  curl "${CURL_ARGS[@]}" \
    -D "${tools_headers}" \
    -o "${tools_body}" \
    -H "Authorization: Bearer ${MCPHUB_BEARER_TOKEN}" \
    -H "Mcp-Session-Id: ${session_id}" \
    -H "MCP-Protocol-Version: ${protocol_version}" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' \
    "${endpoint_url}"

  local -a validation_args=(
    assert-tools
    --headers "${tools_headers}"
    --body "${tools_body}"
    --response-id "${MCP_TOOLS_LIST_ID}"
    --mode "${assertion_mode}"
  )
  local expected_tool
  for expected_tool in "${expected_tools[@]}"; do
    validation_args+=(--expect "${expected_tool}")
  done
  uv run python "${SCRIPT_DIR}/mcp_response.py" "${validation_args[@]}"
}

smoke_endpoint "${MCPHUB_BASE_URL%/}/mcp" "all" "contains"
smoke_endpoint "${MCPHUB_BASE_URL%/}/mcp/ddgs" "ddgs" "exact" "${DDGS_EXPECTED_TOOLS[@]}"
smoke_endpoint "${MCPHUB_BASE_URL%/}/mcp/harness" "harness" "contains" "${DDGS_EXPECTED_TOOLS[@]}"

printf 'MCPHub smoke passed (all + ddgs + harness; DDGS six-tool surface verified)\n'
