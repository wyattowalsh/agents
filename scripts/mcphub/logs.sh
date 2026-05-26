#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

mkdir -p "${MCPHUB_RUN_DIR}"
touch "${MCPHUB_LOG_FILE}"
tail -n "${MCPHUB_LOG_TAIL:-200}" -f "${MCPHUB_LOG_FILE}"
