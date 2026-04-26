#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${AGENTS_REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
MCP_ROOT="${AGENTS_MCP_ROOT:-$REPO_ROOT/mcp}"
SERVERS_DIR="$MCP_ROOT/servers"

mkdir -p "$SERVERS_DIR" "$MCP_ROOT/archives" "$MCP_ROOT/cache" "$MCP_ROOT/notes" "$MCP_ROOT/secrets"

update_repo() {
  local name="$1"
  local url="$2"
  local dir="$SERVERS_DIR/$name"

  if [[ -e "$dir" && ! -d "$dir/.git" ]]; then
    echo "Refusing to update $dir because it exists but is not a git checkout" >&2
    return 1
  fi

  if [[ -d "$dir/.git" ]]; then
    echo "Updating $name"
    git -C "$dir" fetch --prune
    git -C "$dir" pull --ff-only
  else
    echo "Cloning $name"
    git clone "$url" "$dir"
  fi
}

require_file() {
  local path="$1"
  if [[ ! -f "$path" ]]; then
    echo "Missing required file: $path" >&2
    return 1
  fi
}

update_repo "MCP_Atom_of_Thoughts" "https://github.com/kbsooo/MCP_Atom_of_Thoughts.git"
(
  cd "$SERVERS_DIR/MCP_Atom_of_Thoughts"
  npm install
  npm run build
)
require_file "$SERVERS_DIR/MCP_Atom_of_Thoughts/build/index.js"

update_repo "lotus-wisdom-mcp" "https://github.com/linxule/lotus-wisdom-mcp.git"
if [[ ! -f "$SERVERS_DIR/lotus-wisdom-mcp/dist/bundle.js" ]]; then
  (
    cd "$SERVERS_DIR/lotus-wisdom-mcp"
    npm install
    npm run build
  )
fi
require_file "$SERVERS_DIR/lotus-wisdom-mcp/dist/bundle.js"

update_repo "mcp-thinking" "https://github.com/VitalyMalakanov/mcp-thinking.git"
require_file "$SERVERS_DIR/mcp-thinking/enhanced_sequential_thinking_server.py"

echo "MCP installs are up to date under $MCP_ROOT"
