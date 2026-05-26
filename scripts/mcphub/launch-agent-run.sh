#!/usr/bin/env bash
set -euo pipefail

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:${PATH:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

mcphub_load_env
mkdir -p "${MCPHUB_RUN_DIR}"
printf '%s\n' "$$" >"${MCPHUB_PID_FILE}"

launchctl setenv MCPHUB_BASE_URL "${MCPHUB_BASE_URL}" >/dev/null 2>&1 || true
if [[ -n "${MCPHUB_PUBLIC_URL:-}" ]]; then
  launchctl setenv MCPHUB_PUBLIC_URL "${MCPHUB_PUBLIC_URL}" >/dev/null 2>&1 || true
fi
if [[ -n "${MCPHUB_BEARER_TOKEN:-}" ]]; then
  launchctl setenv MCPHUB_BEARER_TOKEN "${MCPHUB_BEARER_TOKEN}" >/dev/null 2>&1 || true
fi

MCPHUB_CHILD_PID=""

cleanup() {
  mcphub_stop_process_tree "${MCPHUB_CHILD_PID}"
  mcphub_stop_tunnel
  rm -f "${MCPHUB_PID_FILE}" "${MCPHUB_CHILD_PID_FILE}"
}
trap cleanup EXIT INT TERM

cd "${MCPHUB_REPO_ROOT}"
npx -y @samanhappy/mcphub &
MCPHUB_CHILD_PID="$!"
printf '%s\n' "${MCPHUB_CHILD_PID}" >"${MCPHUB_CHILD_PID_FILE}"
if mcphub_wait_healthy; then
  mcphub_start_tunnel
fi
wait "${MCPHUB_CHILD_PID}"
