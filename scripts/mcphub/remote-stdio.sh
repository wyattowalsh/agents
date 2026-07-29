#!/usr/bin/env bash
set -euo pipefail

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:${PATH:-}"

if [[ $# -lt 1 ]]; then
  printf 'usage: remote-stdio.sh <mcphub-url>\n' >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/mcphub/common.sh
source "${SCRIPT_DIR}/common.sh"
mcphub_load_env

mcphub_require_token

"${SCRIPT_DIR}/ensure-running.sh"

mcphub_exec_clean MCPHUB_BEARER_TOKEN -- \
  npx -y mcp-remote@0.1.38 "$1" \
  --allow-http \
  --transport http-only \
  --silent \
  --header 'Authorization:Bearer ${MCPHUB_BEARER_TOKEN}'
