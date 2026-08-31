#!/usr/bin/env bash
set -euo pipefail

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:${PATH:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

mcphub_load_env
mcphub_prepare_run_directory
printf '%s\n' "$$" >"${MCPHUB_PID_FILE}"
cd "${MCPHUB_REPO_ROOT}"
exec bash "${SCRIPT_DIR}/start-server.sh"
