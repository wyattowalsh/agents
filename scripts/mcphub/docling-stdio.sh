#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

mcphub_load_env

workdir="${MCPHUB_DOCLING_WORKDIR:-${MCPHUB_RUN_DIR}/docling-workdir}"
mkdir -p "${workdir}"
cd "${workdir}"

unset OPENCODE_SERVER_USERNAME OPENCODE_SERVER_PASSWORD

exec uvx --from "${MCPHUB_DOCLING_PACKAGE:-docling-mcp[local]}" docling-mcp-server --transport stdio "$@"
