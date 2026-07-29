#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

mcphub_load_env

export MODE="${OPEN_WEBSEARCH_MODE:-stdio}"
export DEFAULT_SEARCH_ENGINE="${OPEN_WEBSEARCH_DEFAULT_ENGINE:-duckduckgo}"
export SEARCH_MODE="${OPEN_WEBSEARCH_SEARCH_MODE:-request}"
export ALLOWED_SEARCH_ENGINES="${OPEN_WEBSEARCH_ALLOWED_ENGINES:-duckduckgo,startpage,bing,brave}"

mcphub_exec_clean \
  MODE \
  DEFAULT_SEARCH_ENGINE \
  SEARCH_MODE \
  ALLOWED_SEARCH_ENGINES \
  -- npx -y open-websearch@2.1.11
