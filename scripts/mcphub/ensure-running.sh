#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

mcphub_load_env
if ! mcphub_resolve_remote_mode; then
  printf 'Invalid remote activation detected; removing remote exposure before local-only recovery\n' >&2
  mcphub_stop_tunnel
  mcphub_assert_tunnel_absent
  mcphub_stop_activation_guard
  mcphub_assert_activation_guard_absent
  if mcphub_launch_agent_loaded; then
    mcphub_bootout_launch_agent
    if mcphub_launch_agent_loaded; then
      printf 'MCPHub LaunchAgent remained loaded; local-only recovery is blocked\n' >&2
      exit 1
    fi
  fi
  if mcphub_pid_file_running "${MCPHUB_PID_FILE}"; then
    mcphub_stop_managed_local
  else
    rm -f "${MCPHUB_PID_FILE}"
  fi
  mcphub_runtime_listeners_are_absent
  export MCPHUB_REMOTE_MODE_OVERRIDE=disabled
  export MCPHUB_REMOTE_MODE=disabled
  export MCPHUB_TUNNEL_ENABLED=false
  mcphub_start_local
  mcphub_wait_mode_ready
  mcphub_remote_listener_is_absent
  printf 'Remote activation remains invalid; local-only MCPHub was restored\n' >&2
  exit 1
fi

if mcphub_runtime_is_mode_ready; then
  mcphub_reconcile_remote_exposure
  exit 0
fi

if mcphub_launch_agent_loaded; then
  printf 'MCPHub LaunchAgent is already loaded; waiting for the selected exact route\n' >&2
  if mcphub_wait_mode_ready; then
    mcphub_reconcile_remote_exposure
    exit 0
  fi
  printf 'MCPHub LaunchAgent is loaded but not healthy; not starting a second hub\n' >&2
  printf 'Check %s and just mcphub-doctor.\n' "${MCPHUB_LOG_FILE}" >&2
  exit 1
fi

mcphub_start_local

if mcphub_wait_mode_ready; then
  mcphub_reconcile_remote_exposure
  exit 0
fi

printf 'MCPHub selected runtime did not become ready at %s/mcp/things\n' "${MCPHUB_BASE_URL}" >&2
printf 'Check %s for startup logs.\n' "${MCPHUB_LOG_FILE}" >&2
exit 1
