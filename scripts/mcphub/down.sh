#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

mcphub_load_env

mcphub_stop_tunnel
if ! mcphub_assert_tunnel_absent; then
  printf 'Cloudflare tunnel absence could not be proven; refusing local shutdown\n' >&2
  exit 1
fi
mcphub_stop_activation_guard
if ! mcphub_assert_activation_guard_absent; then
  printf 'activation expiry guard absence could not be proven; refusing local shutdown\n' >&2
  exit 1
fi

if mcphub_launch_agent_loaded; then
  mcphub_bootout_launch_agent
  printf 'stopped MCPHub LaunchAgent\n'
fi

if mcphub_pid_file_running "${MCPHUB_PID_FILE}"; then
  mcphub_stop_managed_local
  printf 'stopped MCPHub local process\n'
else
  rm -f "${MCPHUB_PID_FILE}"
fi
mcphub_release_instance_lock
