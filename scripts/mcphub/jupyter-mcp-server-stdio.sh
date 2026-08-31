#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

mcphub_load_env

if [[ -z "${JUPYTER_URL:-}" || -z "${JUPYTER_TOKEN:-}" ]]; then
  printf 'jupyter-mcp-server requires JUPYTER_URL and JUPYTER_TOKEN in .env.mcphub (server stays enabled; set env to connect).\n' >&2
  exit 1
fi

package="${MCPHUB_JUPYTER_PACKAGE:-jupyter-mcp-server==1.0.2}"
# 1.0.2 imports KernelClient; jupyter-kernel-client 1.x renamed that to
# JupyterKernelClient. Pin 0.x. Also pin mcp 1.x (mcp 2 dropped FastMCP).
mcphub_exec_clean \
  ALLOW_IMG_OUTPUT \
  JUPYTER_DOCUMENT_ID \
  JUPYTER_TOKEN \
  JUPYTER_URL \
  -- uvx --from "${package}" --with "jupyter-kernel-client>=0.9.0,<1" --with "mcp>=1.10.1,<2" jupyter-mcp-server "$@"
