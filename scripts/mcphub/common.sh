#!/usr/bin/env bash
set -euo pipefail

MCPHUB_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCPHUB_REPO_ROOT="$(cd "${MCPHUB_SCRIPT_DIR}/../.." && pwd)"
MCPHUB_ENV_FILE="${MCPHUB_REPO_ROOT}/.env.mcphub"
MCPHUB_DEFAULT_PORT="46683"
MCPHUB_DEFAULT_BASE_PATH=""
MCPHUB_BASE_URL="${MCPHUB_BASE_URL:-}"
MCPHUB_RUN_DIR="${MCPHUB_REPO_ROOT}/.mcphub"
MCPHUB_PID_FILE="${MCPHUB_RUN_DIR}/mcphub.pid"
MCPHUB_CHILD_PID_FILE="${MCPHUB_RUN_DIR}/mcphub-child.pid"
MCPHUB_LOG_FILE="${MCPHUB_RUN_DIR}/mcphub.log"
MCPHUB_SETTING_PATH="${MCPHUB_SETTING_PATH:-${MCPHUB_REPO_ROOT}/mcp/mcphub/mcp_settings.json}"
MCPHUB_TUNNEL_PID_FILE="${MCPHUB_TUNNEL_PID_FILE:-${MCPHUB_RUN_DIR}/cloudflared.pid}"
MCPHUB_TUNNEL_LOG_FILE="${MCPHUB_TUNNEL_LOG_FILE:-${MCPHUB_RUN_DIR}/cloudflared.log}"
MCPHUB_TUNNEL_RUNTIME_CONFIG="${MCPHUB_TUNNEL_RUNTIME_CONFIG:-${MCPHUB_RUN_DIR}/cloudflared.yml}"

mcphub_setup_runtime_path() {
  local home_dir="${HOME:-/Users/ww}"
  local entries=(
    "${home_dir}/.local/share/mise/shims"
    "${home_dir}/.local/bin"
    "${home_dir}/Library/pnpm"
    "/opt/homebrew/bin"
    "/opt/homebrew/sbin"
    "/usr/local/bin"
    "/usr/bin"
    "/bin"
    "/usr/sbin"
    "/sbin"
  )
  local mise_bin=""
  if command -v mise >/dev/null 2>&1; then
    mise_bin="$(command -v mise)"
  elif [[ -x "/opt/homebrew/bin/mise" ]]; then
    mise_bin="/opt/homebrew/bin/mise"
  elif [[ -x "${home_dir}/.local/bin/mise" ]]; then
    mise_bin="${home_dir}/.local/bin/mise"
  fi
  if [[ -n "${mise_bin}" ]]; then
    local tool tool_path
    for tool in node npm npx uv uvx; do
      tool_path="$("${mise_bin}" which "${tool}" 2>/dev/null || true)"
      if [[ -n "${tool_path}" && -x "${tool_path}" ]]; then
        entries=("$(dirname "${tool_path}")" "${entries[@]}")
      fi
    done
  fi

  local new_path="" entry
  for entry in "${entries[@]}"; do
    [[ -d "${entry}" ]] || continue
    case ":${new_path}:${PATH:-}:" in
      *":${entry}:"*) ;;
      *) new_path="${new_path:+${new_path}:}${entry}" ;;
    esac
  done
  export PATH="${new_path:+${new_path}:}${PATH:-}"
}

mcphub_load_env() {
  if [[ -f "${MCPHUB_ENV_FILE}" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "${MCPHUB_ENV_FILE}"
    set +a
  else
    printf 'warning: .env.mcphub is missing; copy .env.mcphub.example and fill local secrets\n' >&2
  fi
  mcphub_setup_runtime_path
  PORT="${PORT:-${MCPHUB_DEFAULT_PORT}}"
  BASE_PATH="${BASE_PATH-${MCPHUB_DEFAULT_BASE_PATH}}"
  MCPHUB_BASE_URL="${MCPHUB_BASE_URL:-http://127.0.0.1:${PORT}${BASE_PATH}}"
  if [[ "${MCPHUB_SETTING_PATH:-}" != /* ]]; then
    MCPHUB_SETTING_PATH="${MCPHUB_REPO_ROOT}/${MCPHUB_SETTING_PATH}"
  fi
  MCPHUB_TUNNEL_TARGET_URL="${MCPHUB_TUNNEL_TARGET_URL:-${MCPHUB_BASE_URL}}"
  MCPHUB_TUNNEL_PROVIDER="${MCPHUB_TUNNEL_PROVIDER:-cloudflare}"
  MCPHUB_TUNNEL_PROTOCOL="${MCPHUB_TUNNEL_PROTOCOL:-http2}"
  MCPHUB_TUNNEL_TOKEN="${MCPHUB_TUNNEL_TOKEN:-}"
  MCPHUB_ZAPIER_WEBHOOK_URL="${MCPHUB_ZAPIER_WEBHOOK_URL:-}"
  export PORT BASE_PATH MCPHUB_BASE_URL MCPHUB_SETTING_PATH MCPHUB_TUNNEL_TARGET_URL
  export MCPHUB_TUNNEL_PROVIDER MCPHUB_TUNNEL_PROTOCOL MCPHUB_TUNNEL_TOKEN MCPHUB_ZAPIER_WEBHOOK_URL
}

mcphub_health_url() {
  printf '%s/health' "${MCPHUB_BASE_URL%/}"
}

mcphub_is_healthy() {
  curl -fsS --max-time 2 "$(mcphub_health_url)" >/dev/null 2>&1
}

mcphub_startup_wait_seconds() {
  if [[ -n "${MCPHUB_STARTUP_WAIT_SECONDS:-}" ]]; then
    printf '%s\n' "${MCPHUB_STARTUP_WAIT_SECONDS}"
    return 0
  fi
  local init_timeout_ms="${INIT_TIMEOUT:-300000}"
  if [[ "${init_timeout_ms}" =~ ^[0-9]+$ ]]; then
    printf '%s\n' $(( (init_timeout_ms + 999) / 1000 ))
  else
    printf '300\n'
  fi
}

mcphub_wait_healthy() {
  local wait_seconds
  wait_seconds="$(mcphub_startup_wait_seconds)"
  for _ in $(seq 1 "${wait_seconds}"); do
    if mcphub_is_healthy; then
      return 0
    fi
    sleep 1
  done
  return 1
}

mcphub_require_token() {
  if [[ -z "${MCPHUB_BEARER_TOKEN:-}" || "${MCPHUB_BEARER_TOKEN}" == replace-with-local-* ]]; then
    printf 'MCPHUB_BEARER_TOKEN is required in .env.mcphub or the environment\n' >&2
    return 1
  fi
}

mcphub_read_pid_file() {
  local pid_file="$1"
  [[ -f "${pid_file}" ]] || return 1
  local pid
  pid="$(tr -d '[:space:]' <"${pid_file}")"
  [[ "${pid}" =~ ^[0-9]+$ ]] || return 1
  printf '%s\n' "${pid}"
}

mcphub_process_command() {
  local pid="$1"
  ps -p "${pid}" -o command= 2>/dev/null || true
}

mcphub_is_managed_local_pid() {
  local pid="$1"
  local command
  command="$(mcphub_process_command "${pid}")"
  case "${command}" in
    *"${MCPHUB_REPO_ROOT}/scripts/mcphub/launch-agent-run.sh"*|*"@samanhappy/mcphub"*|*"/node_modules/.bin/mcphub"*)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

mcphub_pid_file_running() {
  local pid_file="$1"
  local pid
  if ! pid="$(mcphub_read_pid_file "${pid_file}")"; then
    rm -f "${pid_file}"
    return 1
  fi
  kill -0 "${pid}" >/dev/null 2>&1
}

mcphub_pid_file_managed_running() {
  local pid_file="$1"
  local pid
  pid="$(mcphub_read_pid_file "${pid_file}")" || return 1
  kill -0 "${pid}" >/dev/null 2>&1 || return 1
  mcphub_is_managed_local_pid "${pid}"
}

mcphub_pid_running() {
  mcphub_pid_file_running "${MCPHUB_PID_FILE}"
}

mcphub_tunnel_enabled() {
  case "${MCPHUB_TUNNEL_ENABLED:-false}" in
    1|true|TRUE|yes|YES|on|ON) return 0 ;;
    *) return 1 ;;
  esac
}

mcphub_signal_process_tree() {
  local signal="$1"
  local root_pid="$2"
  [[ -n "${root_pid}" ]] || return 0
  local child_pid
  while IFS= read -r child_pid; do
    [[ -n "${child_pid}" ]] || continue
    mcphub_signal_process_tree "${signal}" "${child_pid}"
  done < <(pgrep -P "${root_pid}" 2>/dev/null || true)
  kill "-${signal}" "${root_pid}" >/dev/null 2>&1 || true
}

mcphub_stop_process_tree() {
  local root_pid="$1"
  [[ -n "${root_pid}" ]] || return 0
  kill -0 "${root_pid}" >/dev/null 2>&1 || return 0
  mcphub_signal_process_tree TERM "${root_pid}"
  for _ in $(seq 1 5); do
    kill -0 "${root_pid}" >/dev/null 2>&1 || return 0
    sleep 1
  done
  mcphub_signal_process_tree KILL "${root_pid}"
}

mcphub_stop_pid_file() {
  local pid_file="$1"
  if mcphub_pid_file_running "${pid_file}"; then
    mcphub_stop_process_tree "$(mcphub_read_pid_file "${pid_file}")"
  fi
  rm -f "${pid_file}"
}

mcphub_stop_managed_pid_file() {
  local pid_file="$1"
  local label="$2"
  local pid
  if ! pid="$(mcphub_read_pid_file "${pid_file}")"; then
    rm -f "${pid_file}"
    return 1
  fi
  if ! kill -0 "${pid}" >/dev/null 2>&1; then
    rm -f "${pid_file}"
    return 1
  fi
  if ! mcphub_is_managed_local_pid "${pid}"; then
    printf 'refusing to stop unmanaged MCPHub %s pid %s: %s\n' "${label}" "${pid}" "$(mcphub_process_command "${pid}")" >&2
    return 1
  fi
  mcphub_stop_process_tree "${pid}"
  rm -f "${pid_file}"
}

mcphub_stop_managed_local() {
  mcphub_stop_managed_pid_file "${MCPHUB_CHILD_PID_FILE}" "child" || true
  mcphub_stop_managed_pid_file "${MCPHUB_PID_FILE}" "wrapper" || true
}

mcphub_public_mcp_url() {
  local public_url="${MCPHUB_PUBLIC_URL:-}"
  public_url="${public_url%/}"
  if [[ -z "${public_url}" ]]; then
    return 1
  fi
  if [[ "${public_url}" == */mcp ]]; then
    printf '%s\n' "${public_url}"
  else
    printf '%s/mcp\n' "${public_url}"
  fi
}

mcphub_notify_zapier_tunnel_ready() {
  if [[ -z "${MCPHUB_ZAPIER_WEBHOOK_URL:-}" ]]; then
    return 0
  fi
  local public_mcp_url
  if ! public_mcp_url="$(mcphub_public_mcp_url)"; then
    return 0
  fi
  local timestamp payload
  timestamp="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  payload="$(
    printf '{"event":"mcphub_tunnel_ready","service":"mcphub","public_url":"%s","local_url":"%s","provider":"%s","timestamp":"%s"}' \
      "${public_mcp_url}" \
      "${MCPHUB_BASE_URL%/}/mcp" \
      "${MCPHUB_TUNNEL_PROVIDER}" \
      "${timestamp}"
  )"
  curl -fsS --max-time 10 \
    -H "Content-Type: application/json" \
    -d "${payload}" \
    "${MCPHUB_ZAPIER_WEBHOOK_URL}" >/dev/null 2>&1 || \
    printf 'warning: failed to notify MCPHUB_ZAPIER_WEBHOOK_URL\n' >&2
}

mcphub_generate_cloudflared_config() {
  if [[ -z "${MCPHUB_TUNNEL_NAME:-}" ]]; then
    printf 'MCPHUB_TUNNEL_NAME is required when MCPHUB_TUNNEL_ENABLED=true\n' >&2
    return 1
  fi
  if [[ -z "${MCPHUB_TUNNEL_HOSTNAME:-}" ]]; then
    printf 'MCPHUB_TUNNEL_HOSTNAME is required when MCPHUB_TUNNEL_ENABLED=true\n' >&2
    return 1
  fi
  if [[ -z "${MCPHUB_TUNNEL_CREDENTIALS_FILE:-}" ]]; then
    printf 'MCPHUB_TUNNEL_CREDENTIALS_FILE is required when MCPHUB_TUNNEL_CONFIG is unset\n' >&2
    return 1
  fi
  mkdir -p "${MCPHUB_RUN_DIR}"
  cat >"${MCPHUB_TUNNEL_RUNTIME_CONFIG}" <<EOF
tunnel: ${MCPHUB_TUNNEL_NAME}
credentials-file: ${MCPHUB_TUNNEL_CREDENTIALS_FILE}

ingress:
  - hostname: ${MCPHUB_TUNNEL_HOSTNAME}
    service: ${MCPHUB_TUNNEL_TARGET_URL%/}
    originRequest:
      httpHostHeader: ${MCPHUB_TUNNEL_HOSTNAME}
      connectTimeout: 10s
  - service: http_status:404
EOF
  printf '%s\n' "${MCPHUB_TUNNEL_RUNTIME_CONFIG}"
}

mcphub_start_tunnel() {
  mcphub_tunnel_enabled || return 0
  mkdir -p "${MCPHUB_RUN_DIR}"
  if mcphub_pid_file_running "${MCPHUB_TUNNEL_PID_FILE}"; then
    return 0
  fi
  case "${MCPHUB_TUNNEL_PROVIDER}" in
    cloudflare|cloudflared) ;;
    *)
      printf 'unsupported MCPHUB_TUNNEL_PROVIDER: %s\n' "${MCPHUB_TUNNEL_PROVIDER}" >&2
      return 1
      ;;
  esac
  if ! command -v cloudflared >/dev/null 2>&1; then
    printf 'cloudflared is required when MCPHUB_TUNNEL_ENABLED=true\n' >&2
    return 1
  fi
  if ! mcphub_public_mcp_url >/dev/null; then
    printf 'MCPHUB_PUBLIC_URL is required when MCPHUB_TUNNEL_ENABLED=true\n' >&2
    return 1
  fi

  local config_path public_mcp_url
  public_mcp_url="$(mcphub_public_mcp_url)"
  config_path="${MCPHUB_TUNNEL_CONFIG:-}"
  if [[ -n "${MCPHUB_TUNNEL_TOKEN}" ]]; then
    printf 'starting MCPHub Cloudflare tunnel for %s; logs: %s\n' "${public_mcp_url}" "${MCPHUB_TUNNEL_LOG_FILE}" >&2
    nohup cloudflared tunnel --no-autoupdate --protocol "${MCPHUB_TUNNEL_PROTOCOL}" run --token "${MCPHUB_TUNNEL_TOKEN}" >>"${MCPHUB_TUNNEL_LOG_FILE}" 2>&1 &
    printf '%s\n' "$!" >"${MCPHUB_TUNNEL_PID_FILE}"
    mcphub_notify_zapier_tunnel_ready
    return 0
  elif [[ -z "${config_path}" ]]; then
    config_path="$(mcphub_generate_cloudflared_config)"
  fi

  printf 'starting MCPHub Cloudflare tunnel for %s; logs: %s\n' "${public_mcp_url}" "${MCPHUB_TUNNEL_LOG_FILE}" >&2
  nohup cloudflared tunnel --config "${config_path}" --protocol "${MCPHUB_TUNNEL_PROTOCOL}" run "${MCPHUB_TUNNEL_NAME:-mcphub}" >>"${MCPHUB_TUNNEL_LOG_FILE}" 2>&1 &
  printf '%s\n' "$!" >"${MCPHUB_TUNNEL_PID_FILE}"
  mcphub_notify_zapier_tunnel_ready
}

mcphub_stop_tunnel() {
  mcphub_stop_pid_file "${MCPHUB_TUNNEL_PID_FILE}"
}

mcphub_stop_local() {
  mcphub_stop_managed_local
}

mcphub_start_local() {
  mkdir -p "${MCPHUB_RUN_DIR}"
  if mcphub_is_healthy; then
    return 0
  fi
  if mcphub_pid_running || mcphub_pid_file_running "${MCPHUB_CHILD_PID_FILE}"; then
    local grace_seconds="${MCPHUB_UNHEALTHY_PID_GRACE_SECONDS:-5}"
    sleep "${grace_seconds}"
    if mcphub_is_healthy; then
      return 0
    fi
    printf 'MCPHub pid is present but health failed; stopping managed stale process before restart\n' >&2
    mcphub_stop_managed_local
  fi
  printf 'starting MCPHub locally with npx @samanhappy/mcphub; logs: %s\n' "${MCPHUB_LOG_FILE}" >&2
  (
    cd "${MCPHUB_REPO_ROOT}"
    exec npx -y @samanhappy/mcphub
  ) >>"${MCPHUB_LOG_FILE}" 2>&1 &
  printf '%s\n' "$!" >"${MCPHUB_PID_FILE}"
  rm -f "${MCPHUB_CHILD_PID_FILE}"
}
