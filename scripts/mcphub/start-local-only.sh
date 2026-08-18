#!/usr/bin/env bash
# Start or reuse the loopback MCPHub singleton. Never starts the Cloudflare tunnel.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

export MCPHUB_TUNNEL_ENABLED=false

mcphub_load_env

if mcphub_is_healthy; then
  exit 0
fi

if mcphub_launch_agent_loaded; then
  printf 'MCPHub LaunchAgent is already loaded; waiting for %s\n' "$(mcphub_health_url)" >&2
  if mcphub_wait_healthy; then
    exit 0
  fi
  printf 'MCPHub LaunchAgent is loaded but not healthy; not starting a second hub\n' >&2
  exit 1
fi

mcphub_start_local

if mcphub_wait_healthy; then
  exit 0
fi

printf 'MCPHub did not become healthy at %s\n' "$(mcphub_health_url)" >&2
printf 'Check %s for startup logs.\n' "${MCPHUB_LOG_FILE}" >&2
exit 1
