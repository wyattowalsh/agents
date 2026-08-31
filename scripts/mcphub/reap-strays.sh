#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

mcphub_load_env

pid="$(mcphub_read_pid_file "${MCPHUB_PID_FILE}" 2>/dev/null || true)"
if [[ -z "${pid}" ]]; then
  rm -f "${MCPHUB_PID_FILE}"
  printf 'no tracked MCPHub runtime pid\n'
  exit 0
fi
if ! kill -0 "${pid}" >/dev/null 2>&1; then
  rm -f "${MCPHUB_PID_FILE}"
  printf 'removed one stale MCPHub runtime pid receipt\n'
  exit 0
fi
if ! mcphub_is_managed_local_pid "${pid}"; then
  printf 'tracked MCPHub pid is not the selected downstream; no process was signaled\n' >&2
  exit 1
fi
printf 'tracked selected MCPHub runtime is active; no stray process scan is performed\n'
