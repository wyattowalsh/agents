#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

usage() {
  cat <<'EOF'
Usage: reconcile-runtime.sh [--check] [--restart]

Atomically reconcile tracked MCPHub settings into the private runtime settings
file. It replaces every prior bearer key with the current loopback bearer,
preserves OAuth/client/user collections, and never writes a full private backup.
This command never materializes or selects a downstream distribution.

  --check    Read-only candidate/runtime drift and selected-distribution audit
  --restart  Restart the installed LaunchAgent after reconciliation
EOF
}

CHECK=0
RESTART=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --check) CHECK=1 ;;
    --restart) RESTART=1 ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf 'unknown argument: %s\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

if [[ "${CHECK}" -eq 1 && "${RESTART}" -eq 1 ]]; then
  printf -- '--check is read-only and cannot be combined with --restart\n' >&2
  exit 2
fi

mcphub_load_env
mcphub_require_token
tracked="${MCPHUB_REPO_ROOT}/mcp/mcphub/mcp_settings.json"

if [[ "${CHECK}" -eq 1 ]]; then
  check_status=0
  if ! "${SCRIPT_DIR}/validate-settings.sh" >/dev/null; then
    printf 'tracked MCPHub settings candidate is invalid\n' >&2
    check_status=1
  fi
  if ! uv run python "${SCRIPT_DIR}/reconcile_runtime_settings.py" \
    --tracked "${tracked}" \
    --runtime "${MCPHUB_SETTING_PATH}" \
    --check; then
    check_status=1
  fi
  if mcphub_distribution_is_selected; then
    printf 'selected content-addressed downstream verified\n'
  else
    printf 'selected content-addressed downstream is absent or invalid\n' >&2
    check_status=1
  fi
  exit "${check_status}"
fi

"${SCRIPT_DIR}/validate-settings.sh" >/dev/null
uv run python "${SCRIPT_DIR}/reconcile_runtime_settings.py" \
  --tracked "${tracked}" \
  --runtime "${MCPHUB_SETTING_PATH}"
printf 'reconciled private runtime settings from %s\n' "${tracked}"

if [[ "${RESTART}" -eq 1 ]]; then
  service="gui/$(id -u)/com.wyattowalsh.mcphub"
  if ! launchctl print "${service}" >/dev/null 2>&1; then
    printf 'LaunchAgent %s is not installed; no runtime was started\n' "${service}" >&2
    exit 1
  fi
  launchctl kickstart -k "${service}"
  printf 'restarted com.wyattowalsh.mcphub\n'
fi
