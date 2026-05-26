#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

mcphub_load_env

if mcphub_pid_running || mcphub_pid_file_running "${MCPHUB_CHILD_PID_FILE}"; then
  mcphub_stop_local
  printf 'stopped MCPHub local process\n'
else
  rm -f "${MCPHUB_PID_FILE}" "${MCPHUB_CHILD_PID_FILE}"
  printf 'MCPHub local process is not running\n'
fi
mcphub_stop_tunnel
