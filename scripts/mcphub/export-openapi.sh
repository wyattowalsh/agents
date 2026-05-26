#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

"${SCRIPT_DIR}/ensure-running.sh"
mkdir -p "${MCPHUB_REPO_ROOT}/mcp/mcphub"
curl -fsS "${MCPHUB_BASE_URL%/}/api/openapi.json" \
  -o "${MCPHUB_REPO_ROOT}/mcp/mcphub/openapi.json"
printf 'wrote mcp/mcphub/openapi.json\n'
