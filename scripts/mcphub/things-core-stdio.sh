#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

mcphub_setup_runtime_path
mcphub_load_env

if ! command -v uname >/dev/null 2>&1; then
  printf 'things-core: uname is required to verify the managed platform\n' >&2
  exit 69
fi
if ! command -v uv >/dev/null 2>&1; then
  printf 'things-core: uv is required; install uv and retry\n' >&2
  exit 69
fi
if [[ "$(uname -s)" != "Darwin" || "$(uname -m)" != "arm64" ]]; then
  printf 'things-core: the audited runtime requires arm64 macOS\n' >&2
  exit 69
fi

TUNNEL_ENABLED="${MCPHUB_TUNNEL_ENABLED:-false}"
DEVELOPMENT_OVERRIDE="${THINGS_CORE_ALLOW_UNVERIFIED_ARTIFACT_CACHE:-0}"
if [[ -z "${THINGS_CORE_WHEEL_PATH:-}" || -z "${THINGS_CORE_SDIST_PATH:-}" ]]; then
  if [[ "${DEVELOPMENT_OVERRIDE}" != "1" || "${TUNNEL_ENABLED}" != "false" ]]; then
    printf 'things-core: audited wheel and sdist paths are required; doctor code things_core_distribution_artifacts_missing\n' >&2
    printf 'things-core: a cache-only development override is allowed only with MCPHUB_TUNNEL_ENABLED=false\n' >&2
    exit 78
  fi
fi

CORE_SOURCE="${MCPHUB_REPO_ROOT}/mcp/things-core"
COMMON_SOURCE="${MCPHUB_REPO_ROOT}/packages/things-common"
if [[ ! -f "${CORE_SOURCE}/things_core/server.py" || ! -f "${COMMON_SOURCE}/things_common/__init__.py" ]]; then
  printf 'things-core: repository source package is incomplete\n' >&2
  exit 66
fi

export PYTHON_DOTENV_DISABLED="1"
export MCPHUB_TUNNEL_ENABLED="${TUNNEL_ENABLED}"

mcphub_exec_clean \
  MCPHUB_TUNNEL_ENABLED \
  PYTHON_DOTENV_DISABLED \
  THINGS_CORE_ALLOW_UNVERIFIED_ARTIFACT_CACHE \
  THINGS_CORE_SDIST_PATH \
  THINGS_CORE_WHEEL_PATH \
  THINGS_MCP_ALLOW_LOCAL_IDENTITY_FALLBACK \
  THINGS_MCP_LOCAL_CLIENT_ID \
  THINGS_MCP_LOCAL_PRINCIPAL \
  -- uv run \
  --project "${MCPHUB_REPO_ROOT}" \
  --package mcp-things-core \
  --offline \
  --frozen \
  --no-sync \
  --no-env-file \
  --managed-python \
  --no-python-downloads \
  --python 3.12 \
  python -m things_core.server "$@"
