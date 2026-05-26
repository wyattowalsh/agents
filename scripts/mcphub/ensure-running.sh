#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

mcphub_load_env

if mcphub_is_healthy; then
  mcphub_start_tunnel
  exit 0
fi

mcphub_start_local

if mcphub_wait_healthy; then
  mcphub_start_tunnel
  exit 0
fi

printf 'MCPHub did not become healthy at %s\n' "$(mcphub_health_url)" >&2
printf 'Check %s for startup logs.\n' "${MCPHUB_LOG_FILE}" >&2
exit 1
