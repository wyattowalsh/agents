#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

mcphub_load_env

# Optional elevation secrets are loaded from .env.mcphub when present:
# REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD,
# REDDIT_USER_AGENT, REDDIT_BUDDY_NO_CACHE.
# Anonymous mode works with no credentials (lower rate limits).

mcphub_exec_clean \
  REDDIT_CLIENT_ID \
  REDDIT_CLIENT_SECRET \
  REDDIT_USERNAME \
  REDDIT_PASSWORD \
  REDDIT_USER_AGENT \
  REDDIT_BUDDY_NO_CACHE \
  -- npx -y reddit-mcp-buddy@1.1.13
