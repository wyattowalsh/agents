#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
uv run python "${REPO_ROOT}/scripts/mcphub/validate_settings.py" \
  --settings "${REPO_ROOT}/mcp/mcphub/mcp_settings.json" \
  --registry "${REPO_ROOT}/config/mcp-registry.json"
