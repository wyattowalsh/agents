#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

mcphub_load_env

# scrapling[ai] imports FastMCP from the MCP SDK (mcp.server.fastmcp), not the
# standalone fastmcp package. The [all] extra pulls [ai]+[shell] (mcp>=1.27.0,
# fetchers, Convertor). Do not --with standalone fastmcp; it can shadow the SDK.
# Pin mcp 1.x: scrapling 0.4.10 imports mcp.server.fastmcp. mcp 2.x renamed
# FastMCP to MCPServer and raises ModuleNotFoundError on that import path.
package="${MCPHUB_SCRAPLING_PACKAGE:-scrapling[all]==0.4.10}"
mcphub_exec_clean \
  SSL_CERT_FILE \
  SSL_CERT_DIR \
  REQUESTS_CA_BUNDLE \
  CURL_CA_BUNDLE \
  -- uvx --from "${package}" --with "mcp>=1.27.0,<2" scrapling mcp "$@"
