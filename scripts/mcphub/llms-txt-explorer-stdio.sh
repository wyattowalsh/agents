#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

mcphub_load_env

mcphub_exec_clean -- npx -y @thedaviddias/mcp-llms-txt-explorer@0.2.0
