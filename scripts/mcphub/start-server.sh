#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

if [[ $# -ne 0 ]]; then
  printf 'start-server.sh accepts no runtime arguments\n' >&2
  exit 2
fi
if [[ -n "${NODE_OPTIONS:-}" || -n "${NODE_PATH:-}" ]]; then
  printf 'Node preload and module-path overrides are forbidden for MCPHub\n' >&2
  exit 1
fi

mcphub_load_env
mcphub_resolve_remote_mode
mcphub_require_token
if ! mcphub_distribution_is_selected; then
  printf 'no verified content-addressed MCPHub downstream is selected\n' >&2
  exit 1
fi

exec node --disallow-code-generation-from-strings "${MCPHUB_DOWNSTREAM_LAUNCHER}" \
  --runtime-root "${MCPHUB_DOWNSTREAM_RUNTIME_ROOT}"
