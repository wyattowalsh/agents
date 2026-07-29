#!/usr/bin/env bash
# Launch the qsv MCP server (TypeScript) with local qsv/qsvmcp binary.
# Machine-local build lives under mcp/servers/qsv-agent-skills (gitignored).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

mcphub_setup_runtime_path
mcphub_load_env 2>/dev/null || true

REPO_ROOT="${MCPHUB_REPO_ROOT}"
SERVER_JS="${REPO_ROOT}/mcp/servers/qsv-agent-skills/dist/mcp-server.js"

if [[ ! -f "${SERVER_JS}" ]]; then
  echo "qsv MCP server missing at ${SERVER_JS}" >&2
  echo "Build: sparse-checkout .claude/skills → mcp/servers/qsv-agent-skills && npm install && npm run build" >&2
  exit 1
fi

if [[ -z "${QSV_MCP_BIN_PATH:-}" ]]; then
  if command -v qsvmcp >/dev/null 2>&1; then
    QSV_MCP_BIN_PATH="$(command -v qsvmcp)"
  elif command -v qsv >/dev/null 2>&1; then
    QSV_MCP_BIN_PATH="$(command -v qsv)"
  else
    echo "Neither qsvmcp nor qsv found on PATH; set QSV_MCP_BIN_PATH" >&2
    exit 1
  fi
fi

export QSV_MCP_BIN_PATH
export QSV_MCP_WORKING_DIR="${QSV_MCP_WORKING_DIR:-${REPO_ROOT}}"
# Locked default: repo + ~/dev (plan lock). Override via env when needed.
export QSV_MCP_ALLOWED_DIRS="${QSV_MCP_ALLOWED_DIRS:-${REPO_ROOT}:${HOME}/dev}"
export QSV_MCP_CHECK_UPDATES_ON_STARTUP="${QSV_MCP_CHECK_UPDATES_ON_STARTUP:-false}"
export QSV_MCP_OPERATION_TIMEOUT_MS="${QSV_MCP_OPERATION_TIMEOUT_MS:-600000}"

mcphub_exec_clean \
  QSV_MCP_BIN_PATH \
  QSV_MCP_ALLOWED_DIRS \
  QSV_MCP_WORKING_DIR \
  QSV_MCP_CHECK_UPDATES_ON_STARTUP \
  QSV_MCP_OPERATION_TIMEOUT_MS \
  -- node "${SERVER_JS}" "$@"
