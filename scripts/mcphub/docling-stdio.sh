#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

mcphub_load_env

workdir="${MCPHUB_DOCLING_WORKDIR:-${MCPHUB_RUN_DIR}/docling-workdir}"
mkdir -p "${workdir}"
cd "${workdir}"

package="${MCPHUB_DOCLING_PACKAGE:-docling-mcp[local]}"
mcphub_exec_clean \
  SSL_CERT_FILE \
  SSL_CERT_DIR \
  REQUESTS_CA_BUNDLE \
  CURL_CA_BUNDLE \
  -- uvx --from "${package}" docling-mcp-server --transport stdio "$@"
