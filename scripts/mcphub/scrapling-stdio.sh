#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

mcphub_load_env

package="${MCPHUB_SCRAPLING_PACKAGE:-scrapling[ai]==0.4.10}"
mcphub_exec_clean \
  SSL_CERT_FILE \
  SSL_CERT_DIR \
  REQUESTS_CA_BUNDLE \
  CURL_CA_BUNDLE \
  -- uvx --from "${package}" scrapling mcp "$@"
