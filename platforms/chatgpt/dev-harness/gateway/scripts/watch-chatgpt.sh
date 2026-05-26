#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$HOME/Library/Logs/dev-harness-chatgpt"
mkdir -p "$LOG_DIR"

GATEWAY_PID=""
TUNNEL_PID=""

is_chatgpt_running() {
  pgrep -x ChatGPT >/dev/null 2>&1 || pgrep -f '/Applications/ChatGPT.app' >/dev/null 2>&1
}

start_stack() {
  if [[ -z "${GATEWAY_PID}" ]] || ! kill -0 "$GATEWAY_PID" >/dev/null 2>&1; then
    "$DIR/scripts/start-gateway.sh" >>"$LOG_DIR/gateway.log" 2>&1 &
    GATEWAY_PID="$!"
    echo "started gateway pid=$GATEWAY_PID" >>"$LOG_DIR/watcher.log"
  fi

  if [[ -z "${TUNNEL_PID}" ]] || ! kill -0 "$TUNNEL_PID" >/dev/null 2>&1; then
    "$DIR/scripts/start-tunnel.sh" >>"$LOG_DIR/tunnel.log" 2>&1 &
    TUNNEL_PID="$!"
    echo "started tunnel pid=$TUNNEL_PID" >>"$LOG_DIR/watcher.log"
  fi
}

stop_stack() {
  if [[ -n "${TUNNEL_PID}" ]] && kill -0 "$TUNNEL_PID" >/dev/null 2>&1; then
    kill "$TUNNEL_PID" || true
    wait "$TUNNEL_PID" 2>/dev/null || true
    echo "stopped tunnel pid=$TUNNEL_PID" >>"$LOG_DIR/watcher.log"
  fi
  TUNNEL_PID=""

  if [[ -n "${GATEWAY_PID}" ]] && kill -0 "$GATEWAY_PID" >/dev/null 2>&1; then
    kill "$GATEWAY_PID" || true
    wait "$GATEWAY_PID" 2>/dev/null || true
    echo "stopped gateway pid=$GATEWAY_PID" >>"$LOG_DIR/watcher.log"
  fi
  GATEWAY_PID=""
}

cleanup() {
  stop_stack
}
trap cleanup EXIT INT TERM

while true; do
  if is_chatgpt_running; then
    start_stack
  else
    stop_stack
  fi
  sleep 5
done
