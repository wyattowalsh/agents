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

if [[ -z "${MCPHUB_BEARER_TOKEN:-}" ]]; then
  printf 'MCPHUB_BEARER_TOKEN is required for MCPHub stdio bridge\n' >&2
  exit 1
fi

"${SCRIPT_DIR}/ensure-running.sh"

exec npx -y mcp-remote@latest "$1" --allow-http --transport http-only --silent --header "Authorization: Bearer ${MCPHUB_BEARER_TOKEN}"
