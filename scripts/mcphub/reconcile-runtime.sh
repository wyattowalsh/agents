#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

usage() {
  cat <<'EOF'
Usage: reconcile-runtime.sh [--warm] [--restart]

Copy tracked mcp/mcphub/mcp_settings.json into .mcphub/runtime/mcp_settings.json,
optionally warm package-version-check-mcp, and restart the local LaunchAgent.

  --warm     Run package-version-check-mcp launcher --help before restart
  --restart  kickstart com.wyattowalsh.mcphub (default when any flag is set)
EOF
}

WARM=0
RESTART=0
for arg in "$@"; do
  case "${arg}" in
    --warm) WARM=1 ;;
    --restart) RESTART=1 ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      printf 'unknown argument: %s\n' "${arg}" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ "${WARM}" -eq 0 && "${RESTART}" -eq 0 ]]; then
  WARM=1
  RESTART=1
fi

mcphub_load_env

tracked="${MCPHUB_REPO_ROOT}/mcp/mcphub/mcp_settings.json"
runtime="${MCPHUB_REPO_ROOT}/.mcphub/runtime/mcp_settings.json"
mkdir -p "$(dirname "${runtime}")"
/bin/cp -f "${tracked}" "${runtime}"
printf 'synced runtime settings from %s\n' "${tracked}"

launcher="${SCRIPT_DIR}/package-version-check-mcp.sh"
if [[ "${WARM}" -eq 1 && -x "${launcher}" ]]; then
  printf 'warming package-version-check-mcp launcher...\n'
  "${launcher}" --help >/dev/null
  printf 'launcher warm ok\n'
fi

if [[ "${RESTART}" -eq 1 ]]; then
  launchctl kickstart -k "gui/$(id -u)/com.wyattowalsh.mcphub"
  printf 'restarted com.wyattowalsh.mcphub\n'
fi