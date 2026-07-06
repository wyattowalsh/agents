#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

mcphub_load_env

unset OPENCODE_SERVER_USERNAME OPENCODE_SERVER_PASSWORD

exec uvx --from "${MCPHUB_SCRAPLING_PACKAGE:-scrapling[ai]==0.4.10}" scrapling mcp "$@"