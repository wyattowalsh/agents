#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${AGENTS_REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
MCP_ROOT="${AGENTS_MCP_ROOT:-$REPO_ROOT/mcp}"
SERVER_DIR="$MCP_ROOT/servers/mcp-thinking"
CACHE_DIR="$MCP_ROOT/cache"
LOG_FILE="$CACHE_DIR/mcp-thinking.log"

if [[ ! -f "$SERVER_DIR/enhanced_sequential_thinking_server.py" ]]; then
  echo "mcp-thinking checkout is missing at $SERVER_DIR" >&2
  echo "Run: $REPO_ROOT/scripts/mcp_tools/update_installed_mcps.sh" >&2
  exit 1
fi

mkdir -p "$CACHE_DIR"

PORT="${MCP_THINKING_PORT:-}"
if [[ -z "$PORT" ]]; then
  PORT="$(python3 - <<'PY'
import socket

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.bind(("127.0.0.1", 0))
    print(sock.getsockname()[1])
PY
)"
fi

server_pid=""
cleanup() {
  if [[ -n "$server_pid" ]]; then
    kill "$server_pid" >/dev/null 2>&1 || true
    wait "$server_pid" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT INT TERM

(
  cd "$SERVER_DIR"
  MCP_SERVER_PORT="$PORT" uv run --no-project \
    --with 'fastmcp==2.3.0' \
    --with 'mcp[cli]' \
    --with fastapi \
    --with uvicorn \
    --with colorama \
    --with numpy \
    --with scikit-learn \
    --with textstat \
    python enhanced_sequential_thinking_server.py
) >>"$LOG_FILE" 2>&1 &
server_pid="$!"

for _ in $(seq 1 80); do
  if python3 - "$PORT" <<'PY' >/dev/null 2>&1
import socket
import sys

try:
    with socket.create_connection(("127.0.0.1", int(sys.argv[1])), timeout=0.2):
        pass
except OSError:
    sys.exit(1)
PY
  then
    exec uvx mcp-proxy --log-level WARNING "http://127.0.0.1:$PORT/sse"
  fi
  if ! kill -0 "$server_pid" >/dev/null 2>&1; then
    echo "mcp-thinking server exited before readiness. See $LOG_FILE" >&2
    exit 1
  fi
  sleep 0.25
done

echo "Timed out waiting for mcp-thinking on http://127.0.0.1:$PORT/sse. See $LOG_FILE" >&2
exit 1
