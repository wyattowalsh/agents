#!/usr/bin/env bash
# Start or reuse the loopback MCPHub singleton. Never starts the Cloudflare tunnel.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

mcphub_load_env
export MCPHUB_REMOTE_MODE_OVERRIDE=disabled
mcphub_resolve_remote_mode

mcphub_stop_tunnel
mcphub_assert_tunnel_absent
mcphub_stop_activation_guard
mcphub_assert_activation_guard_absent

local_only_ready() {
  mcphub_runtime_is_mode_ready
}

if local_only_ready; then
  exit 0
fi

if mcphub_launch_agent_loaded; then
  printf 'MCPHub LaunchAgent is already loaded; waiting for the selected exact route\n' >&2
  if mcphub_wait_mode_ready; then
    exit 0
  fi
  printf 'MCPHub LaunchAgent is loaded but not healthy; not starting a second hub\n' >&2
  exit 1
fi

mcphub_start_local

if mcphub_wait_mode_ready; then
  exit 0
fi

printf 'MCPHub selected runtime did not become ready at %s/mcp/things\n' "${MCPHUB_BASE_URL}" >&2
printf 'Check %s for startup logs.\n' "${MCPHUB_LOG_FILE}" >&2
exit 1
