#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

mcphub_load_env

package="${MCPHUB_JUPYTER_PACKAGE:-jupyter-mcp-server==1.0.2}"
mcphub_exec_clean \
  ALLOW_IMG_OUTPUT \
  JUPYTER_DOCUMENT_ID \
  JUPYTER_TOKEN \
  JUPYTER_URL \
  -- uvx --from "${package}" jupyter-mcp-server "$@"
