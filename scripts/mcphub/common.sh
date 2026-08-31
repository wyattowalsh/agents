#!/usr/bin/env bash
set -euo pipefail

MCPHUB_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCPHUB_REPO_ROOT="$(cd "${MCPHUB_SCRIPT_DIR}/../.." && pwd)"
MCPHUB_ENV_FILE="${MCPHUB_REPO_ROOT}/.env.mcphub"
MCPHUB_RUN_DIR="${MCPHUB_REPO_ROOT}/.mcphub"
MCPHUB_PID_FILE="${MCPHUB_RUN_DIR}/mcphub.pid"
MCPHUB_LOG_FILE="${MCPHUB_RUN_DIR}/mcphub.log"
MCPHUB_INSTANCE_LOCK="${MCPHUB_INSTANCE_LOCK:-${MCPHUB_RUN_DIR}/instance.lock}"
MCPHUB_TUNNEL_PID_FILE="${MCPHUB_TUNNEL_PID_FILE:-${MCPHUB_RUN_DIR}/cloudflared.pid}"
MCPHUB_TUNNEL_IDENTITY_FILE="${MCPHUB_TUNNEL_IDENTITY_FILE:-${MCPHUB_RUN_DIR}/cloudflared.identity}"
MCPHUB_TUNNEL_LOG_FILE="${MCPHUB_TUNNEL_LOG_FILE:-${MCPHUB_RUN_DIR}/cloudflared.log}"
MCPHUB_TUNNEL_RUNTIME_CONFIG="${MCPHUB_TUNNEL_RUNTIME_CONFIG:-${MCPHUB_RUN_DIR}/cloudflared.yml}"
MCPHUB_ACTIVATION_GUARD_PID_FILE="${MCPHUB_ACTIVATION_GUARD_PID_FILE:-${MCPHUB_RUN_DIR}/activation-expiry-guard.pid}"
MCPHUB_ACTIVATION_GUARD_IDENTITY_FILE="${MCPHUB_ACTIVATION_GUARD_IDENTITY_FILE:-${MCPHUB_RUN_DIR}/activation-expiry-guard.identity}"
MCPHUB_ACTIVATION_GUARD_LOG_FILE="${MCPHUB_ACTIVATION_GUARD_LOG_FILE:-${MCPHUB_RUN_DIR}/activation-expiry-guard.log}"
MCPHUB_LAUNCH_AGENT_PLIST="${MCPHUB_LAUNCH_AGENT_PLIST:-${HOME}/Library/LaunchAgents/com.wyattowalsh.mcphub.plist}"
MCPHUB_DOWNSTREAM_LAUNCHER="${MCPHUB_REPO_ROOT}/scripts/mcphub/downstream-launch.mjs"
MCPHUB_REMOTE_ACTIVATION_HELPER="${MCPHUB_REPO_ROOT}/scripts/mcphub/remote-activation.mjs"
MCPHUB_ACTIVATION_GUARD_SCRIPT="${MCPHUB_REPO_ROOT}/scripts/mcphub/activation-expiry-guard.sh"

mcphub_setup_runtime_path() {
  local home_dir="${HOME:-}"
  local entries=(
    "/opt/homebrew/bin"
    "/opt/homebrew/sbin"
    "/usr/local/bin"
    "/usr/bin"
    "/bin"
    "/usr/sbin"
    "/sbin"
  )
  if [[ -n "${home_dir}" ]]; then
    entries=(
      "${home_dir}/.local/share/mise/shims"
      "${home_dir}/.local/bin"
      "${home_dir}/Library/pnpm"
      "${entries[@]}"
    )
  fi
  local mise_bin=""
  if command -v mise >/dev/null 2>&1; then
    mise_bin="$(command -v mise)"
  elif [[ -x "/opt/homebrew/bin/mise" ]]; then
    mise_bin="/opt/homebrew/bin/mise"
  elif [[ -n "${home_dir}" && -x "${home_dir}/.local/bin/mise" ]]; then
    mise_bin="${home_dir}/.local/bin/mise"
  fi
  if [[ -n "${mise_bin}" ]]; then
    local tool tool_path
    for tool in node uv uvx; do
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
  local inherited_remote_mode_set="${MCPHUB_REMOTE_MODE+x}"
  local inherited_remote_mode="${MCPHUB_REMOTE_MODE-}"
  local inherited_remote_mode_override_set="${MCPHUB_REMOTE_MODE_OVERRIDE+x}"
  local inherited_remote_mode_override="${MCPHUB_REMOTE_MODE_OVERRIDE-}"
  local inherited_observed_evidence_set="${MCPHUB_REMOTE_OBSERVED_WIRE_EVIDENCE_PATH+x}"
  local inherited_observed_evidence="${MCPHUB_REMOTE_OBSERVED_WIRE_EVIDENCE_PATH-}"
  if [[ -f "${MCPHUB_ENV_FILE}" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "${MCPHUB_ENV_FILE}"
    set +a
  else
    printf 'warning: .env.mcphub is missing; copy .env.mcphub.example and fill local secrets\n' >&2
  fi
  if [[ "${inherited_remote_mode_set}" == "x" ]]; then
    MCPHUB_REMOTE_MODE="${inherited_remote_mode}"
  fi
  if [[ "${inherited_remote_mode_override_set}" == "x" ]]; then
    MCPHUB_REMOTE_MODE_OVERRIDE="${inherited_remote_mode_override}"
  fi
  if [[ "${inherited_observed_evidence_set}" == "x" ]]; then
    MCPHUB_REMOTE_OBSERVED_WIRE_EVIDENCE_PATH="${inherited_observed_evidence}"
  fi
  mcphub_setup_runtime_path

  PORT="${PORT:-46683}"
  MCPHUB_REMOTE_PORT="${MCPHUB_REMOTE_PORT:-46684}"
  MCPHUB_BIND_HOST="${MCPHUB_BIND_HOST:-127.0.0.1}"
  MCPHUB_BASE_URL="${MCPHUB_BASE_URL:-http://127.0.0.1:46683}"
  MCPHUB_REMOTE_BASE_URL="${MCPHUB_REMOTE_BASE_URL:-http://127.0.0.1:46684}"
  MCPHUB_PUBLIC_URL="${MCPHUB_PUBLIC_URL:-https://mcp.w4w.dev/mcp/things}"
  MCPHUB_TUNNEL_TARGET_URL="${MCPHUB_TUNNEL_TARGET_URL:-http://127.0.0.1:46684}"
  MCPHUB_DOWNSTREAM_RUNTIME_ROOT="${MCPHUB_DOWNSTREAM_RUNTIME_ROOT:-${MCPHUB_RUN_DIR}/downstream}"
  MCPHUB_SETTING_PATH="${MCPHUB_SETTING_PATH:-${MCPHUB_RUN_DIR}/runtime/mcp_settings.json}"
  MCPHUB_REMOTE_ACTIVATION_RECEIPT_PATH="${MCPHUB_REMOTE_ACTIVATION_RECEIPT_PATH:-${MCPHUB_RUN_DIR}/remote-activation.json}"
  MCPHUB_REMOTE_CAPTURE_RECEIPT_PATH="${MCPHUB_REMOTE_CAPTURE_RECEIPT_PATH:-${MCPHUB_RUN_DIR}/remote-capture-activation.json}"
  MCPHUB_REMOTE_CONFORMANCE_RESULT_PATH="${MCPHUB_REMOTE_CONFORMANCE_RESULT_PATH:-${MCPHUB_REPO_ROOT}/mcp/mcphub/downstream/fixtures/protocol/conformance-report.json}"
  MCPHUB_REMOTE_CAPTURE_EVIDENCE_PATH="${MCPHUB_REMOTE_CAPTURE_EVIDENCE_PATH:-${MCPHUB_RUN_DIR}/remote-capture-evidence.json}"
  MCPHUB_REMOTE_OBSERVED_WIRE_EVIDENCE_PATH="${MCPHUB_REMOTE_OBSERVED_WIRE_EVIDENCE_PATH:-}"
  MCPHUB_OAUTH_POLICY_PATH="${MCPHUB_OAUTH_POLICY_PATH:-}"
  MCPHUB_OAUTH_LOGIN_CREDENTIAL_PATH="${MCPHUB_OAUTH_LOGIN_CREDENTIAL_PATH:-}"
  MCPHUB_REMOTE_MODE="${MCPHUB_REMOTE_MODE:-disabled}"
  MCPHUB_TUNNEL_PROVIDER="${MCPHUB_TUNNEL_PROVIDER:-cloudflare}"
  MCPHUB_TUNNEL_PROTOCOL="${MCPHUB_TUNNEL_PROTOCOL:-http2}"
  MCPHUB_TUNNEL_TOKEN="${MCPHUB_TUNNEL_TOKEN:-}"
  MCPHUB_ZAPIER_WEBHOOK_URL="${MCPHUB_ZAPIER_WEBHOOK_URL:-}"
  REPO_ROOT="${REPO_ROOT:-${MCPHUB_REPO_ROOT}}"

  if [[ "${PORT}" != "46683" || "${MCPHUB_REMOTE_PORT}" != "46684" || "${MCPHUB_BIND_HOST}" != "127.0.0.1" ]]; then
    printf 'MCPHub listener identities are fixed at 127.0.0.1:46683 and 127.0.0.1:46684\n' >&2
    return 1
  fi
  if [[ "${MCPHUB_BASE_URL}" != "http://127.0.0.1:46683" || "${MCPHUB_REMOTE_BASE_URL}" != "http://127.0.0.1:46684" ]]; then
    printf 'MCPHub listener resource origins are fixed\n' >&2
    return 1
  fi
  if [[ "${MCPHUB_PUBLIC_URL}" != "https://mcp.w4w.dev/mcp/things" || "${MCPHUB_TUNNEL_TARGET_URL}" != "http://127.0.0.1:46684" ]]; then
    printf 'MCPHub public Things route or remote tunnel target drifted\n' >&2
    return 1
  fi
  if [[ "${MCPHUB_DOWNSTREAM_RUNTIME_ROOT}" != /* \
    || "${MCPHUB_SETTING_PATH}" != /* \
    || "${MCPHUB_REMOTE_ACTIVATION_RECEIPT_PATH}" != /* \
    || "${MCPHUB_REMOTE_CAPTURE_RECEIPT_PATH}" != /* \
    || "${MCPHUB_REMOTE_CONFORMANCE_RESULT_PATH}" != /* \
    || "${MCPHUB_REMOTE_CAPTURE_EVIDENCE_PATH}" != /* \
    || "${MCPHUB_TUNNEL_RUNTIME_CONFIG}" != /* ]]; then
    printf 'MCPHub runtime, settings, receipt, evidence, and ingress paths must be absolute\n' >&2
    return 1
  fi
  case "${MCPHUB_REMOTE_MODE}" in
    disabled|capture|public) ;;
    *)
      printf 'MCPHUB_REMOTE_MODE must be disabled, capture, or public\n' >&2
      return 1
      ;;
  esac

  export PORT MCPHUB_REMOTE_PORT MCPHUB_BIND_HOST MCPHUB_BASE_URL MCPHUB_REMOTE_BASE_URL
  export MCPHUB_PUBLIC_URL MCPHUB_TUNNEL_TARGET_URL MCPHUB_DOWNSTREAM_RUNTIME_ROOT
  export MCPHUB_SETTING_PATH MCPHUB_REMOTE_ACTIVATION_RECEIPT_PATH
  export MCPHUB_REMOTE_CAPTURE_RECEIPT_PATH MCPHUB_REMOTE_MODE
  export MCPHUB_REMOTE_MODE_OVERRIDE
  export MCPHUB_REMOTE_CONFORMANCE_RESULT_PATH MCPHUB_REMOTE_CAPTURE_EVIDENCE_PATH
  export MCPHUB_REMOTE_OBSERVED_WIRE_EVIDENCE_PATH MCPHUB_OAUTH_POLICY_PATH
  export MCPHUB_OAUTH_LOGIN_CREDENTIAL_PATH MCPHUB_TUNNEL_RUNTIME_CONFIG
  export MCPHUB_TUNNEL_PROVIDER MCPHUB_TUNNEL_PROTOCOL
  export MCPHUB_TUNNEL_TOKEN MCPHUB_ZAPIER_WEBHOOK_URL REPO_ROOT
}

mcphub_require_token() {
  if [[ -z "${MCPHUB_BEARER_TOKEN:-}" \
    || "${MCPHUB_BEARER_TOKEN}" == replace-with-local-* \
    || "${MCPHUB_BEARER_TOKEN}" == "\${MCPHUB_BEARER_TOKEN}" ]]; then
    printf 'MCPHUB_BEARER_TOKEN is required in .env.mcphub or the environment\n' >&2
    return 1
  fi
}

mcphub_exec_clean() {
  local -a allowlist=()
  while [[ $# -gt 0 && "$1" != "--" ]]; do
    if [[ ! "$1" =~ ^[A-Z_][A-Z0-9_]*$ ]]; then
      printf 'invalid MCPHub environment allowlist name: %s\n' "$1" >&2
      return 64
    fi
    allowlist+=("$1")
    shift
  done
  if [[ $# -eq 0 || "$1" != "--" ]]; then
    printf 'usage: mcphub_exec_clean [ENV_VAR ...] -- command [args ...]\n' >&2
    return 64
  fi
  shift
  if [[ $# -eq 0 ]]; then
    printf 'mcphub_exec_clean requires a command\n' >&2
    return 64
  fi
  local -a clean_env=(
    "HOME=${HOME:-}"
    "PATH=${PATH:-/usr/bin:/bin:/usr/sbin:/sbin}"
    "TMPDIR=${TMPDIR:-/tmp}"
    "LANG=${LANG:-C}"
    "LC_ALL=${LC_ALL:-}"
    "USER=${USER:-}"
    "LOGNAME=${LOGNAME:-}"
    "SHELL=${SHELL:-/bin/sh}"
  )
  local name value
  for name in "${allowlist[@]}"; do
    if value="$(/usr/bin/printenv "${name}")"; then
      clean_env+=("${name}=${value}")
    fi
  done
  exec /usr/bin/env -i "${clean_env[@]}" "$@"
}

mcphub_run_clean() {
  local -a allowlist=()
  while [[ $# -gt 0 && "$1" != "--" ]]; do
    if [[ ! "$1" =~ ^[A-Z_][A-Z0-9_]*$ ]]; then
      printf 'invalid MCPHub environment allowlist name: %s\n' "$1" >&2
      return 64
    fi
    allowlist+=("$1")
    shift
  done
  if [[ $# -eq 0 || "$1" != "--" ]]; then
    printf 'usage: mcphub_run_clean [ENV_VAR ...] -- command [args ...]\n' >&2
    return 64
  fi
  shift
  if [[ $# -eq 0 ]]; then
    printf 'mcphub_run_clean requires a command\n' >&2
    return 64
  fi
  local -a clean_env=(
    "HOME=${HOME:-}"
    "PATH=${PATH:-/usr/bin:/bin:/usr/sbin:/sbin}"
    "TMPDIR=${TMPDIR:-/tmp}"
    "LANG=${LANG:-C}"
    "LC_ALL=${LC_ALL:-}"
    "USER=${USER:-}"
    "LOGNAME=${LOGNAME:-}"
    "SHELL=${SHELL:-/bin/sh}"
  )
  local name value
  for name in "${allowlist[@]}"; do
    if value="$(/usr/bin/printenv "${name}")"; then
      clean_env+=("${name}=${value}")
    fi
  done
  /usr/bin/env -i "${clean_env[@]}" "$@"
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
  # macOS `ps -o command=` truncates; `-www` keeps the managed argv intact.
  ps -www -p "$1" -o command= 2>/dev/null || true
}

mcphub_process_identity() {
  local pid="$1" marker process_stat
  [[ "${pid}" =~ ^[0-9]+$ ]] || return 1
  kill -0 "${pid}" >/dev/null 2>&1 || return 1

  if [[ -r "/proc/${pid}/stat" ]]; then
    process_stat="$(<"/proc/${pid}/stat")"
    process_stat="${process_stat##*) }"
    marker="$(awk '{print $20}' <<<"${process_stat}")"
    [[ "${marker}" =~ ^[0-9]+$ ]] || return 1
    printf '%s|linux-start-ticks:%s\n' "${pid}" "${marker}"
    return 0
  fi

  marker="$(LC_ALL=C ps -p "${pid}" -o lstart= 2>/dev/null)" || return 1
  marker="$(awk '{$1 = $1; print}' <<<"${marker}")"
  [[ -n "${marker}" ]] || return 1
  printf '%s|ps-lstart:%s\n' "${pid}" "${marker}"
}

mcphub_is_managed_local_pid() {
  local command
  command="$(mcphub_process_command "$1")"
  case "${command}" in
    node\ --disallow-code-generation-from-strings\ "${MCPHUB_DOWNSTREAM_LAUNCHER}"\ --runtime-root\ "${MCPHUB_DOWNSTREAM_RUNTIME_ROOT}"|\
    */node\ --disallow-code-generation-from-strings\ "${MCPHUB_DOWNSTREAM_LAUNCHER}"\ --runtime-root\ "${MCPHUB_DOWNSTREAM_RUNTIME_ROOT}")
      return 0
      ;;
    *) return 1 ;;
  esac
}

mcphub_managed_local_identity() {
  local pid="$1" identity_before identity_after
  identity_before="$(mcphub_process_identity "${pid}")" || return 1
  mcphub_is_managed_local_pid "${pid}" || return 1
  identity_after="$(mcphub_process_identity "${pid}")" || return 1
  [[ "${identity_after}" == "${identity_before}" ]] || return 1
  printf '%s\n' "${identity_before}"
}

mcphub_pid_file_running() {
  local pid_file="$1" pid
  pid="$(mcphub_read_pid_file "${pid_file}")" || return 1
  kill -0 "${pid}" >/dev/null 2>&1
}

mcphub_pid_file_managed_running() {
  local pid_file="$1" pid
  pid="$(mcphub_read_pid_file "${pid_file}")" || return 1
  mcphub_managed_local_identity "${pid}" >/dev/null
}

mcphub_launch_agent_label() {
  printf 'gui/%s/com.wyattowalsh.mcphub\n' "$(id -u)"
}

mcphub_launch_agent_loaded() {
  command -v launchctl >/dev/null 2>&1 || return 1
  launchctl print "$(mcphub_launch_agent_label)" >/dev/null 2>&1
}

mcphub_bootout_launch_agent() {
  mcphub_launch_agent_loaded || return 0
  launchctl bootout "gui/$(id -u)" "${MCPHUB_LAUNCH_AGENT_PLIST}" >/dev/null 2>&1 || \
    launchctl bootout "$(mcphub_launch_agent_label)" >/dev/null 2>&1 || true
  local attempt
  for ((attempt = 0; attempt < 15; attempt += 1)); do
    if ! mcphub_launch_agent_loaded; then
      return 0
    fi
    sleep 1
  done
  printf 'MCPHub LaunchAgent remained loaded after bootout\n' >&2
  return 1
}

mcphub_reap_stale_instance_lock() {
  [[ -e "${MCPHUB_INSTANCE_LOCK}" || -L "${MCPHUB_INSTANCE_LOCK}" ]] || return 0
  [[ -f "${MCPHUB_INSTANCE_LOCK}" && ! -L "${MCPHUB_INSTANCE_LOCK}" && -O "${MCPHUB_INSTANCE_LOCK}" ]] || return 1
  local owner_pid owner_identity receipt receipt_suffix claim current_pid current_identity current_receipt
  owner_pid="$(sed -n '1p' "${MCPHUB_INSTANCE_LOCK}" 2>/dev/null || true)"
  owner_identity="$(sed -n '2p' "${MCPHUB_INSTANCE_LOCK}" 2>/dev/null || true)"
  receipt="$(sed -n '3p' "${MCPHUB_INSTANCE_LOCK}" 2>/dev/null || true)"
  [[ "${owner_pid}" =~ ^[0-9]+$ && "${owner_identity}" == "${owner_pid}|"* ]] || return 1
  case "${receipt}" in
    "${MCPHUB_INSTANCE_LOCK}.owner.${owner_pid}."*) ;;
    *) return 1 ;;
  esac
  receipt_suffix="${receipt#"${MCPHUB_INSTANCE_LOCK}.owner.${owner_pid}."}"
  [[ "${receipt_suffix}" =~ ^[0-9]+$ ]] || return 1
  claim="${receipt}/claim"
  [[ -d "${receipt}" && ! -L "${receipt}" && -O "${receipt}" ]] || return 1
  [[ -f "${claim}" && ! -L "${claim}" && -O "${claim}" ]] || return 1
  [[ "${MCPHUB_INSTANCE_LOCK}" -ef "${claim}" ]] || return 1
  if kill -0 "${owner_pid}" >/dev/null 2>&1; then
    return 1
  fi
  current_pid="$(sed -n '1p' "${claim}" 2>/dev/null || true)"
  current_identity="$(sed -n '2p' "${claim}" 2>/dev/null || true)"
  current_receipt="$(sed -n '3p' "${claim}" 2>/dev/null || true)"
  [[ "${current_pid}" == "${owner_pid}" \
    && "${current_identity}" == "${owner_identity}" \
    && "${current_receipt}" == "${receipt}" ]] || return 1
  [[ "${MCPHUB_INSTANCE_LOCK}" -ef "${claim}" ]] || return 1
  if kill -0 "${owner_pid}" >/dev/null 2>&1; then
    return 1
  fi
  rm -f "${MCPHUB_INSTANCE_LOCK}"
  rm -f "${claim}"
  rmdir "${receipt}" 2>/dev/null || return 1
  [[ ! -e "${MCPHUB_INSTANCE_LOCK}" && ! -L "${MCPHUB_INSTANCE_LOCK}" ]]
}

mcphub_acquire_instance_lock() {
  mcphub_prepare_run_directory
  local owner_pid owner_identity receipt claim attempt
  owner_pid="${BASHPID:-$$}"
  owner_identity="$(mcphub_process_identity "${owner_pid}")" || return 1
  for attempt in 0 1; do
    receipt="${MCPHUB_INSTANCE_LOCK}.owner.${owner_pid}.${RANDOM}"
    claim="${receipt}/claim"
    mkdir "${receipt}" 2>/dev/null || return 1
    if ! (umask 077 && printf '%s\n%s\n%s\n' "${owner_pid}" "${owner_identity}" "${receipt}" >"${claim}"); then
      rm -f "${claim}"
      rmdir "${receipt}" 2>/dev/null || true
      return 1
    fi
    if ln "${claim}" "${MCPHUB_INSTANCE_LOCK}" 2>/dev/null; then
      return 0
    fi
    rm -f "${claim}"
    rmdir "${receipt}" 2>/dev/null || true
    if [[ "${attempt}" -eq 0 ]] && mcphub_reap_stale_instance_lock; then
      continue
    fi
    return 1
  done
  return 1
}

mcphub_release_instance_lock() {
  local owner_pid owner_identity current_identity receipt
  [[ -f "${MCPHUB_INSTANCE_LOCK}" ]] || return 0
  owner_pid="$(sed -n '1p' "${MCPHUB_INSTANCE_LOCK}" 2>/dev/null || true)"
  owner_identity="$(sed -n '2p' "${MCPHUB_INSTANCE_LOCK}" 2>/dev/null || true)"
  receipt="$(sed -n '3p' "${MCPHUB_INSTANCE_LOCK}" 2>/dev/null || true)"
  case "${receipt}" in
    "${MCPHUB_INSTANCE_LOCK}.owner."*) ;;
    *) return 1 ;;
  esac
  [[ "${MCPHUB_INSTANCE_LOCK}" -ef "${receipt}/claim" ]] || return 1
  [[ "${owner_pid}" == "${BASHPID:-$$}" ]] || return 1
  current_identity="$(mcphub_process_identity "${owner_pid}" 2>/dev/null || true)"
  [[ -n "${owner_identity}" && "${current_identity}" == "${owner_identity}" ]] || return 1
  rm -f "${MCPHUB_INSTANCE_LOCK}"
  rm -f "${receipt}/claim"
  rmdir "${receipt}" 2>/dev/null || true
}

mcphub_distribution_is_selected() {
  command -v node >/dev/null 2>&1 || return 1
  node "${MCPHUB_DOWNSTREAM_LAUNCHER}" \
    --runtime-root "${MCPHUB_DOWNSTREAM_RUNTIME_ROOT}" \
    --check >/dev/null 2>&1
}

mcphub_listener_endpoints() {
  local port="$1"
  command -v lsof >/dev/null 2>&1 || return 1
  lsof -nP -iTCP:"${port}" -sTCP:LISTEN -F n 2>/dev/null | awk '/^n/ {sub(/^n/, ""); print}'
}

mcphub_listener_pids() {
  local port="$1"
  command -v lsof >/dev/null 2>&1 || return 1
  lsof -nP -iTCP:"${port}" -sTCP:LISTEN -F p 2>/dev/null | awk '
    /^p/ {
      sub(/^p/, "")
      if (!seen[$0]++) print
    }
  '
}

mcphub_listener_is_loopback() {
  local port="$1" endpoints endpoint
  endpoints="$(mcphub_listener_endpoints "${port}")" || return 1
  [[ -n "${endpoints}" ]] || return 1
  while IFS= read -r endpoint; do
    case "${endpoint}" in
      "127.0.0.1:${port}") ;;
      *) return 1 ;;
    esac
  done <<<"${endpoints}"
}

mcphub_listener_is_absent() {
  local port="$1" output="" lsof_status=0
  command -v lsof >/dev/null 2>&1 || return 1
  if output="$(lsof -nP -iTCP:"${port}" -sTCP:LISTEN -F n 2>/dev/null)"; then
    lsof_status=0
  else
    lsof_status=$?
  fi
  [[ "${lsof_status}" -eq 1 && -z "${output}" ]]
}

mcphub_runtime_listeners_are_absent() {
  mcphub_listener_is_absent "${PORT}" \
    && mcphub_listener_is_absent "${MCPHUB_REMOTE_PORT}"
}

mcphub_remote_listener_is_absent() {
  mcphub_listener_is_absent "${MCPHUB_REMOTE_PORT}"
}

mcphub_listener_owned_by_pid() {
  local port="$1" expected_pid="$2" pids pid found=0
  [[ "${expected_pid}" =~ ^[0-9]+$ ]] || return 1
  pids="$(mcphub_listener_pids "${port}")" || return 1
  [[ -n "${pids}" ]] || return 1
  while IFS= read -r pid; do
    [[ "${pid}" == "${expected_pid}" ]] || return 1
    found=1
  done <<<"${pids}"
  [[ "${found}" -eq 1 ]]
}

mcphub_local_route_is_ready() {
  mcphub_require_token >/dev/null 2>&1 || return 1
  local response
  response="$(curl -sS --max-time 2 -o /dev/null -D - \
    -H "Authorization: Bearer ${MCPHUB_BEARER_TOKEN}" \
    --write-out $'\nMCPHUB_STATUS:%{http_code}\nMCPHUB_SIZE:%{size_download}\n' \
    "${MCPHUB_BASE_URL}/mcp/things" 2>/dev/null)" || return 1
  printf '%s\n' "${response}" | awk '
    BEGIN { status = 0; allow = 0 }
    /^MCPHUB_STATUS:405$/ { status = 1 }
    /^MCPHUB_SIZE:0$/ { size = 1 }
    tolower($0) ~ /^allow:[[:space:]]*post\r?$/ { allow = 1 }
    END { exit !(status && allow && size) }
  '
}

mcphub_runtime_is_ready() {
  local pid
  pid="$(mcphub_read_pid_file "${MCPHUB_PID_FILE}")" || return 1
  mcphub_pid_file_managed_running "${MCPHUB_PID_FILE}" && \
    mcphub_listener_is_loopback "${PORT}" && \
    mcphub_listener_owned_by_pid "${PORT}" "${pid}" && \
    mcphub_local_route_is_ready
}

mcphub_wait_ready() {
  local wait_seconds="${MCPHUB_STARTUP_WAIT_SECONDS:-300}"
  [[ "${wait_seconds}" =~ ^[0-9]+$ ]] || return 1
  mcphub_distribution_is_selected || return 1
  local attempt
  for ((attempt = 0; attempt < wait_seconds; attempt += 1)); do
    if mcphub_runtime_is_ready; then
      return 0
    fi
    sleep 1
  done
  return 1
}

mcphub_stop_managed_local() {
  local expected_identity="${1:-}" only_if_unready="${2:-false}"
  local pid signal_identity current_identity current_pid
  pid="$(mcphub_read_pid_file "${MCPHUB_PID_FILE}" 2>/dev/null || true)"
  if [[ -z "${pid}" ]]; then
    rm -f "${MCPHUB_PID_FILE}"
    return 0
  fi
  if ! kill -0 "${pid}" >/dev/null 2>&1; then
    rm -f "${MCPHUB_PID_FILE}"
    return 0
  fi
  signal_identity="$(mcphub_managed_local_identity "${pid}" 2>/dev/null || true)"
  if [[ -z "${signal_identity}" ]]; then
    printf 'refusing to stop unmanaged MCPHub pid %s\n' "${pid}" >&2
    return 1
  fi
  if [[ -n "${expected_identity}" && "${signal_identity}" != "${expected_identity}" ]]; then
    printf 'MCPHub process identity changed before stop; refusing signal\n' >&2
    return 1
  fi
  if [[ "${only_if_unready}" == "true" ]] && mcphub_runtime_is_mode_ready; then
    printf 'tracked MCPHub runtime became ready; preserving it\n' >&2
    return 2
  fi
  current_pid="$(mcphub_read_pid_file "${MCPHUB_PID_FILE}" 2>/dev/null || true)"
  current_identity="$(mcphub_managed_local_identity "${pid}" 2>/dev/null || true)"
  if [[ "${current_pid}" != "${pid}" || "${current_identity}" != "${signal_identity}" ]]; then
    printf 'MCPHub process identity changed immediately before stop; refusing signal\n' >&2
    return 1
  fi
  kill -TERM "${pid}"
  local attempt
  for ((attempt = 0; attempt < 10; attempt += 1)); do
    current_identity="$(mcphub_process_identity "${pid}" 2>/dev/null || true)"
    [[ -n "${current_identity}" ]] || break
    if [[ "${current_identity}" != "${signal_identity}" ]]; then
      printf 'MCPHub pid %s was reused after SIGTERM; preserving its receipt\n' "${pid}" >&2
      return 1
    fi
    sleep 1
  done
  current_identity="$(mcphub_process_identity "${pid}" 2>/dev/null || true)"
  if [[ "${current_identity}" == "${signal_identity}" ]]; then
    printf 'managed MCPHub pid %s did not stop after SIGTERM; sending SIGKILL\n' "${pid}" >&2
    kill -KILL "${pid}" >/dev/null 2>&1 || true
    for ((attempt = 0; attempt < 5; attempt += 1)); do
      current_identity="$(mcphub_process_identity "${pid}" 2>/dev/null || true)"
      [[ -n "${current_identity}" ]] || break
      if [[ "${current_identity}" != "${signal_identity}" ]]; then
        printf 'MCPHub pid %s was reused after SIGKILL; preserving its receipt\n' "${pid}" >&2
        return 1
      fi
      sleep 1
    done
    current_identity="$(mcphub_process_identity "${pid}" 2>/dev/null || true)"
    if [[ "${current_identity}" == "${signal_identity}" ]]; then
      printf 'managed MCPHub pid %s did not stop after SIGKILL\n' "${pid}" >&2
      return 1
    fi
  fi
  if [[ -n "${current_identity}" ]]; then
    printf 'MCPHub pid %s was reused while stopping; preserving its receipt\n' "${pid}" >&2
    return 1
  fi
  current_pid="$(mcphub_read_pid_file "${MCPHUB_PID_FILE}" 2>/dev/null || true)"
  if [[ "${current_pid}" != "${pid}" ]]; then
    printf 'MCPHub pid receipt changed while stopping; preserving it\n' >&2
    return 1
  fi
  rm -f "${MCPHUB_PID_FILE}"
}

mcphub_tunnel_enabled() {
  [[ "${MCPHUB_TUNNEL_ENABLED:-false}" == "true" ]]
}

mcphub_private_file_mode() {
  local path="$1" mode=""
  if mode="$(stat -c '%a' "${path}" 2>/dev/null)"; then
    :
  elif mode="$(/usr/bin/stat -f '%Lp' "${path}" 2>/dev/null)"; then
    :
  else
    return 1
  fi
  printf '%s\n' "${mode}"
}

mcphub_prepare_run_directory() {
  if [[ ! -e "${MCPHUB_RUN_DIR}" && ! -L "${MCPHUB_RUN_DIR}" ]]; then
    (umask 077 && mkdir -p "${MCPHUB_RUN_DIR}")
  fi
  [[ -d "${MCPHUB_RUN_DIR}" && ! -L "${MCPHUB_RUN_DIR}" && -O "${MCPHUB_RUN_DIR}" ]] || return 1
  chmod 700 "${MCPHUB_RUN_DIR}"
  [[ "$(mcphub_private_file_mode "${MCPHUB_RUN_DIR}")" == "700" ]]
}

mcphub_write_private_text() {
  local path="$1" value="$2" parent temporary mode
  parent="$(dirname "${path}")"
  mkdir -p "${parent}"
  [[ -d "${parent}" && ! -L "${parent}" && -O "${parent}" ]] || return 1
  [[ ! -e "${path}" && ! -L "${path}" ]] || return 1
  temporary="${path}.tmp.${BASHPID:-$$}.${RANDOM}"
  (
    umask 077
    printf '%s\n' "${value}" >"${temporary}"
  )
  chmod 600 "${temporary}"
  mv -f "${temporary}" "${path}"
  [[ -f "${path}" && ! -L "${path}" && -O "${path}" ]] || return 1
  mode="$(mcphub_private_file_mode "${path}")" || return 1
  [[ "${mode}" == "600" && "$(cat "${path}")" == "${value}" ]]
}

mcphub_activation_receipt_unexpired() {
  local expected_mode="${1:-}"
  command -v node >/dev/null 2>&1 || return 1
  [[ "${expected_mode}" == "capture" || "${expected_mode}" == "public" ]] || return 1
  node "${MCPHUB_REMOTE_ACTIVATION_HELPER}" unexpired \
    --receipt "${MCPHUB_REMOTE_ACTIVATION_RECEIPT_PATH}" \
    --expect-mode "${expected_mode}"
}

mcphub_remote_activation_mode() {
  command -v node >/dev/null 2>&1 || return 1
  local -a arguments=(
    verify
    --receipt "${MCPHUB_REMOTE_ACTIVATION_RECEIPT_PATH}" \
    --runtime-root "${MCPHUB_DOWNSTREAM_RUNTIME_ROOT}" \
    --settings "${MCPHUB_SETTING_PATH}" \
    --cloudflared-config "${MCPHUB_TUNNEL_RUNTIME_CONFIG}"
    --conformance-result "${MCPHUB_REMOTE_CONFORMANCE_RESULT_PATH}"
    --capture-receipt "${MCPHUB_REMOTE_CAPTURE_RECEIPT_PATH}"
  )
  if [[ -n "${MCPHUB_OAUTH_POLICY_PATH:-}" ]]; then
    arguments+=(--oauth-policy "${MCPHUB_OAUTH_POLICY_PATH}")
  fi
  if [[ -n "${MCPHUB_OAUTH_LOGIN_CREDENTIAL_PATH:-}" ]]; then
    arguments+=(--oauth-login-credential "${MCPHUB_OAUTH_LOGIN_CREDENTIAL_PATH}")
  fi
  if [[ -n "${MCPHUB_REMOTE_OBSERVED_WIRE_EVIDENCE_PATH:-}" ]]; then
    arguments+=(--observed-wire-evidence "${MCPHUB_REMOTE_OBSERVED_WIRE_EVIDENCE_PATH}")
  fi
  node "${MCPHUB_REMOTE_ACTIVATION_HELPER}" "${arguments[@]}"
}

mcphub_resolve_remote_mode() {
  if [[ "${MCPHUB_REMOTE_MODE_OVERRIDE:-}" == "disabled" ]]; then
    MCPHUB_REMOTE_MODE=disabled
    MCPHUB_TUNNEL_ENABLED=false
    export MCPHUB_REMOTE_MODE MCPHUB_TUNNEL_ENABLED
    return 0
  fi

  local requested_mode="${MCPHUB_REMOTE_MODE}" receipt_mode=""
  if [[ "${requested_mode}" == "disabled" ]]; then
    MCPHUB_TUNNEL_ENABLED=false
    export MCPHUB_REMOTE_MODE MCPHUB_TUNNEL_ENABLED
    return 0
  fi
  if [[ -e "${MCPHUB_REMOTE_ACTIVATION_RECEIPT_PATH}" \
    || -L "${MCPHUB_REMOTE_ACTIVATION_RECEIPT_PATH}" ]]; then
    receipt_mode="$(mcphub_remote_activation_mode)" || {
      printf 'MCPHub remote activation receipt is invalid; remote startup is blocked\n' >&2
      return 1
    }
    case "${receipt_mode}" in
      capture|public) ;;
      *)
        printf 'MCPHub remote activation helper returned an invalid mode\n' >&2
        return 1
        ;;
    esac
    if [[ "${requested_mode}" != "${receipt_mode}" ]]; then
      printf 'MCPHub requested remote mode does not match the verified activation receipt\n' >&2
      return 1
    fi
    MCPHUB_REMOTE_MODE="${receipt_mode}"
  elif [[ "${MCPHUB_REMOTE_MODE}" != "disabled" ]]; then
    printf 'MCPHub remote mode requires a verified activation receipt\n' >&2
    return 1
  fi
  if [[ "${MCPHUB_REMOTE_MODE}" == "capture" || "${MCPHUB_REMOTE_MODE}" == "public" ]]; then
    MCPHUB_TUNNEL_ENABLED=true
  else
    MCPHUB_TUNNEL_ENABLED=false
  fi
  export MCPHUB_REMOTE_MODE MCPHUB_TUNNEL_ENABLED
}

mcphub_remote_public_ready() {
  [[ "${MCPHUB_REMOTE_MODE}" == "public" ]] || return 1
  [[ "$(mcphub_remote_activation_mode 2>/dev/null)" == "public" ]] || return 1
  local pid
  pid="$(mcphub_read_pid_file "${MCPHUB_PID_FILE}")" || return 1
  mcphub_pid_file_managed_running "${MCPHUB_PID_FILE}" && \
    mcphub_listener_is_loopback "${MCPHUB_REMOTE_PORT}" && \
    mcphub_listener_owned_by_pid "${MCPHUB_REMOTE_PORT}" "${pid}"
}

mcphub_remote_capture_ready() {
  [[ "${MCPHUB_REMOTE_MODE}" == "capture" ]] || return 1
  [[ "$(mcphub_remote_activation_mode 2>/dev/null)" == "capture" ]] || return 1
  local pid
  pid="$(mcphub_read_pid_file "${MCPHUB_PID_FILE}")" || return 1
  mcphub_pid_file_managed_running "${MCPHUB_PID_FILE}" && \
    mcphub_listener_is_loopback "${MCPHUB_REMOTE_PORT}" && \
    mcphub_listener_owned_by_pid "${MCPHUB_REMOTE_PORT}" "${pid}"
}

mcphub_wait_remote_ready() {
  local expected_mode="$1" wait_seconds="${MCPHUB_STARTUP_WAIT_SECONDS:-300}" attempt
  [[ "${expected_mode}" == "capture" || "${expected_mode}" == "public" ]] || return 1
  [[ "${wait_seconds}" =~ ^[0-9]+$ ]] || return 1
  mcphub_distribution_is_selected || return 1
  for ((attempt = 0; attempt < wait_seconds; attempt += 1)); do
    if [[ "${expected_mode}" == "capture" ]] && mcphub_remote_capture_ready; then
      return 0
    fi
    if [[ "${expected_mode}" == "public" ]] && mcphub_remote_public_ready; then
      return 0
    fi
    sleep 1
  done
  return 1
}

mcphub_runtime_is_mode_ready() {
  mcphub_runtime_is_ready || return 1
  case "${MCPHUB_REMOTE_MODE:-disabled}" in
    disabled)
      ! mcphub_listener_is_loopback "${MCPHUB_REMOTE_PORT:-46684}"
      ;;
    capture)
      mcphub_remote_capture_ready
      ;;
    public)
      mcphub_remote_public_ready
      ;;
    *) return 1 ;;
  esac
}

mcphub_wait_mode_ready() {
  local wait_seconds="${MCPHUB_STARTUP_WAIT_SECONDS:-300}" attempt
  [[ "${wait_seconds}" =~ ^[0-9]+$ ]] || return 1
  mcphub_distribution_is_selected || return 1
  for ((attempt = 0; attempt < wait_seconds; attempt += 1)); do
    if mcphub_runtime_is_mode_ready; then
      return 0
    fi
    sleep 1
  done
  return 1
}

mcphub_wait_runtime_after_start() {
  case "${MCPHUB_REMOTE_MODE:-disabled}" in
    capture|public)
      mcphub_wait_ready
      ;;
    *)
      mcphub_wait_mode_ready
      ;;
  esac
}

mcphub_generate_cloudflared_config() {
  [[ -n "${MCPHUB_TUNNEL_NAME:-}" && -n "${MCPHUB_TUNNEL_HOSTNAME:-}" ]] || return 1
  [[ "${MCPHUB_TUNNEL_HOSTNAME}" == "mcp.w4w.dev" ]] || return 1
  [[ -n "${MCPHUB_TUNNEL_CREDENTIALS_FILE:-}" ]] || return 1
  command -v node >/dev/null 2>&1 || return 1
  mcphub_prepare_run_directory
  node "${MCPHUB_REMOTE_ACTIVATION_HELPER}" render-config \
    --output "${MCPHUB_TUNNEL_RUNTIME_CONFIG}" \
    --tunnel-name "${MCPHUB_TUNNEL_NAME}" \
    --credentials-file "${MCPHUB_TUNNEL_CREDENTIALS_FILE}" >/dev/null
  printf '%s\n' "${MCPHUB_TUNNEL_RUNTIME_CONFIG}"
}

mcphub_verify_cloudflared_config() {
  [[ -n "${MCPHUB_TUNNEL_NAME:-}" && -n "${MCPHUB_TUNNEL_CREDENTIALS_FILE:-}" ]] || return 1
  command -v node >/dev/null 2>&1 || return 1
  node "${MCPHUB_REMOTE_ACTIVATION_HELPER}" verify-config \
    --input "${MCPHUB_TUNNEL_RUNTIME_CONFIG}" \
    --tunnel-name "${MCPHUB_TUNNEL_NAME}" \
    --credentials-file "${MCPHUB_TUNNEL_CREDENTIALS_FILE}" >/dev/null
}

mcphub_is_managed_tunnel_pid() {
  local command
  command="$(mcphub_process_command "$1")"
  case "${command}" in
    cloudflared\ tunnel\ --config\ "${MCPHUB_TUNNEL_RUNTIME_CONFIG}"\ --protocol\ "${MCPHUB_TUNNEL_PROTOCOL}"\ run\ "${MCPHUB_TUNNEL_NAME:-}"|\
    */cloudflared\ tunnel\ --config\ "${MCPHUB_TUNNEL_RUNTIME_CONFIG}"\ --protocol\ "${MCPHUB_TUNNEL_PROTOCOL}"\ run\ "${MCPHUB_TUNNEL_NAME:-}")
      return 0
      ;;
    *) return 1 ;;
  esac
}

mcphub_is_activation_guard_pid() {
  local pid="$1" expected_digest="${2:-}" command digest
  command="$(mcphub_process_command "${pid}")"
  case "${command}" in
    bash\ "${MCPHUB_ACTIVATION_GUARD_SCRIPT}"\ --receipt\ "${MCPHUB_REMOTE_ACTIVATION_RECEIPT_PATH}"\ --receipt-sha256\ *|\
    */bash\ "${MCPHUB_ACTIVATION_GUARD_SCRIPT}"\ --receipt\ "${MCPHUB_REMOTE_ACTIVATION_RECEIPT_PATH}"\ --receipt-sha256\ *)
      digest="${command##* }"
      [[ "${digest}" =~ ^[0-9a-f]{64}$ ]] || return 1
      [[ -z "${expected_digest}" || "${digest}" == "${expected_digest}" ]]
      ;;
    *) return 1 ;;
  esac
}

mcphub_activation_guard_pid_running() {
  local expected_digest="${1:-}" pid expected_identity current_identity
  [[ -f "${MCPHUB_ACTIVATION_GUARD_PID_FILE}" \
    && ! -L "${MCPHUB_ACTIVATION_GUARD_PID_FILE}" \
    && -O "${MCPHUB_ACTIVATION_GUARD_PID_FILE}" \
    && "$(mcphub_private_file_mode "${MCPHUB_ACTIVATION_GUARD_PID_FILE}")" == "600" ]] || return 1
  pid="$(mcphub_read_pid_file "${MCPHUB_ACTIVATION_GUARD_PID_FILE}")" || return 1
  [[ -f "${MCPHUB_ACTIVATION_GUARD_IDENTITY_FILE}" \
    && ! -L "${MCPHUB_ACTIVATION_GUARD_IDENTITY_FILE}" \
    && -O "${MCPHUB_ACTIVATION_GUARD_IDENTITY_FILE}" \
    && "$(mcphub_private_file_mode "${MCPHUB_ACTIVATION_GUARD_IDENTITY_FILE}")" == "600" ]] || return 1
  expected_identity="$(cat "${MCPHUB_ACTIVATION_GUARD_IDENTITY_FILE}")"
  current_identity="$(mcphub_process_identity "${pid}" 2>/dev/null || true)"
  [[ -n "${expected_identity}" && "${current_identity}" == "${expected_identity}" ]] || return 1
  mcphub_is_activation_guard_pid "${pid}" "${expected_digest}"
}

mcphub_managed_activation_guard_process_absent() {
  command -v pgrep >/dev/null 2>&1 || return 1
  local pids="" pgrep_status=0 pid
  if pids="$(pgrep -x bash 2>/dev/null)"; then
    pgrep_status=0
  else
    pgrep_status=$?
  fi
  if [[ "${pgrep_status}" -eq 1 && -z "${pids}" ]]; then
    return 0
  fi
  [[ "${pgrep_status}" -eq 0 && -n "${pids}" ]] || return 1
  while IFS= read -r pid; do
    [[ "${pid}" =~ ^[0-9]+$ ]] || return 1
    if mcphub_is_activation_guard_pid "${pid}"; then
      return 1
    fi
  done <<<"${pids}"
  return 0
}

mcphub_assert_activation_guard_absent() {
  [[ ! -e "${MCPHUB_ACTIVATION_GUARD_PID_FILE}" \
    && ! -L "${MCPHUB_ACTIVATION_GUARD_PID_FILE}" ]] || return 1
  [[ ! -e "${MCPHUB_ACTIVATION_GUARD_IDENTITY_FILE}" \
    && ! -L "${MCPHUB_ACTIVATION_GUARD_IDENTITY_FILE}" ]] || return 1
  mcphub_managed_activation_guard_process_absent
}

mcphub_activation_receipt_digest() {
  command -v node >/dev/null 2>&1 || return 1
  node "${MCPHUB_REMOTE_ACTIVATION_HELPER}" receipt-digest \
    --receipt "${MCPHUB_REMOTE_ACTIVATION_RECEIPT_PATH}"
}

mcphub_tunnel_pid_running() {
  local pid expected_identity current_identity
  [[ -f "${MCPHUB_TUNNEL_PID_FILE}" \
    && ! -L "${MCPHUB_TUNNEL_PID_FILE}" \
    && -O "${MCPHUB_TUNNEL_PID_FILE}" \
    && "$(mcphub_private_file_mode "${MCPHUB_TUNNEL_PID_FILE}")" == "600" ]] || return 1
  pid="$(mcphub_read_pid_file "${MCPHUB_TUNNEL_PID_FILE}")" || return 1
  [[ -f "${MCPHUB_TUNNEL_IDENTITY_FILE}" \
    && ! -L "${MCPHUB_TUNNEL_IDENTITY_FILE}" \
    && -O "${MCPHUB_TUNNEL_IDENTITY_FILE}" \
    && "$(mcphub_private_file_mode "${MCPHUB_TUNNEL_IDENTITY_FILE}")" == "600" ]] || return 1
  expected_identity="$(cat "${MCPHUB_TUNNEL_IDENTITY_FILE}")"
  current_identity="$(mcphub_process_identity "${pid}" 2>/dev/null || true)"
  [[ -n "${expected_identity}" && "${current_identity}" == "${expected_identity}" ]] || return 1
  mcphub_is_managed_tunnel_pid "${pid}"
}

mcphub_managed_tunnel_process_absent() {
  command -v pgrep >/dev/null 2>&1 || return 1
  local pids="" pgrep_status=0 pid
  if pids="$(pgrep -x cloudflared 2>/dev/null)"; then
    pgrep_status=0
  else
    pgrep_status=$?
  fi
  if [[ "${pgrep_status}" -eq 1 && -z "${pids}" ]]; then
    return 0
  fi
  [[ "${pgrep_status}" -eq 0 && -n "${pids}" ]] || return 1
  while IFS= read -r pid; do
    [[ "${pid}" =~ ^[0-9]+$ ]] || return 1
    if mcphub_is_managed_tunnel_pid "${pid}"; then
      return 1
    fi
  done <<<"${pids}"
  return 0
}

mcphub_assert_tunnel_absent() {
  [[ ! -e "${MCPHUB_TUNNEL_PID_FILE}" && ! -L "${MCPHUB_TUNNEL_PID_FILE}" ]] || return 1
  [[ ! -e "${MCPHUB_TUNNEL_IDENTITY_FILE}" && ! -L "${MCPHUB_TUNNEL_IDENTITY_FILE}" ]] || return 1
  mcphub_managed_tunnel_process_absent
}

mcphub_start_tunnel() {
  mcphub_tunnel_enabled || return 0
  case "${MCPHUB_REMOTE_MODE:-disabled}" in
    capture)
      if ! mcphub_remote_capture_ready; then
        printf 'capture MCPHub is not receipt-bound and listening; tunnel remains disabled\n' >&2
        return 1
      fi
      ;;
    public)
      if ! mcphub_remote_public_ready; then
        printf 'remote MCPHub is not stamped, dispatch-enabled, and listening; tunnel remains disabled\n' >&2
        return 1
      fi
      ;;
    *)
      printf 'Cloudflare exposure is forbidden without capture or public receipt mode\n' >&2
      return 1
      ;;
  esac
  if [[ -n "${MCPHUB_TUNNEL_TOKEN}" ]]; then
    printf 'token-only Cloudflare launch cannot prove the frozen ingress manifest\n' >&2
    return 1
  fi
  if ! command -v cloudflared >/dev/null 2>&1; then
    printf 'cloudflared is required when MCPHUB_TUNNEL_ENABLED=true\n' >&2
    return 1
  fi
  if mcphub_tunnel_pid_running; then
    return 0
  fi
  mcphub_assert_tunnel_absent || {
    printf 'an untracked or stale managed tunnel exists; refusing a second connector\n' >&2
    return 1
  }
  mcphub_verify_cloudflared_config || {
    printf 'Cloudflare ingress config failed exact 46684-only readback\n' >&2
    return 1
  }
  local config_path pid identity current_identity
  config_path="${MCPHUB_TUNNEL_RUNTIME_CONFIG}"
  nohup cloudflared tunnel --config "${config_path}" --protocol "${MCPHUB_TUNNEL_PROTOCOL}" \
    run "${MCPHUB_TUNNEL_NAME}" </dev/null >>"${MCPHUB_TUNNEL_LOG_FILE}" 2>&1 &
  pid="$!"
  identity="$(mcphub_process_identity "${pid}" 2>/dev/null || true)"
  if [[ -z "${identity}" ]] || ! mcphub_is_managed_tunnel_pid "${pid}"; then
    [[ -z "${identity}" ]] || kill -TERM "${pid}" >/dev/null 2>&1 || true
    printf 'Cloudflare tunnel process identity could not be verified\n' >&2
    return 1
  fi
  if ! mcphub_write_private_text "${MCPHUB_TUNNEL_PID_FILE}" "${pid}" \
    || ! mcphub_write_private_text "${MCPHUB_TUNNEL_IDENTITY_FILE}" "${identity}" \
    || ! mcphub_tunnel_pid_running; then
    current_identity="$(mcphub_process_identity "${pid}" 2>/dev/null || true)"
    if [[ "${current_identity}" == "${identity}" ]] && mcphub_is_managed_tunnel_pid "${pid}"; then
      kill -TERM "${pid}" >/dev/null 2>&1 || true
    fi
    rm -f "${MCPHUB_TUNNEL_PID_FILE}" "${MCPHUB_TUNNEL_IDENTITY_FILE}"
    printf 'Cloudflare tunnel identity receipt publication failed\n' >&2
    return 1
  fi
}

mcphub_stop_tunnel() {
  local pid expected_identity current_identity attempt wait_seconds
  if [[ -e "${MCPHUB_TUNNEL_PID_FILE}" || -L "${MCPHUB_TUNNEL_PID_FILE}" ]]; then
    [[ -f "${MCPHUB_TUNNEL_PID_FILE}" \
      && ! -L "${MCPHUB_TUNNEL_PID_FILE}" \
      && -O "${MCPHUB_TUNNEL_PID_FILE}" \
      && "$(mcphub_private_file_mode "${MCPHUB_TUNNEL_PID_FILE}")" == "600" ]] || {
      printf 'tunnel pid receipt ownership or mode is invalid\n' >&2
      return 1
    }
  fi
  pid="$(mcphub_read_pid_file "${MCPHUB_TUNNEL_PID_FILE}" 2>/dev/null || true)"
  if [[ -z "${pid}" ]]; then
    if ! mcphub_managed_tunnel_process_absent; then
      printf 'managed tunnel process is present without a valid pid receipt\n' >&2
      return 1
    fi
    rm -f "${MCPHUB_TUNNEL_PID_FILE}" "${MCPHUB_TUNNEL_IDENTITY_FILE}"
    mcphub_assert_tunnel_absent
    return
  fi
  if ! mcphub_tunnel_pid_running; then
    current_identity="$(mcphub_process_identity "${pid}" 2>/dev/null || true)"
    if [[ -n "${current_identity}" ]]; then
      printf 'refusing to stop tunnel pid %s without an exact identity receipt\n' "${pid}" >&2
      return 1
    fi
    if ! mcphub_managed_tunnel_process_absent; then
      printf 'managed tunnel process remains after its tracked pid exited\n' >&2
      return 1
    fi
    rm -f "${MCPHUB_TUNNEL_PID_FILE}" "${MCPHUB_TUNNEL_IDENTITY_FILE}"
    mcphub_assert_tunnel_absent
    return
  fi
  expected_identity="$(cat "${MCPHUB_TUNNEL_IDENTITY_FILE}")"
  current_identity="$(mcphub_process_identity "${pid}")" || return 1
  [[ "${current_identity}" == "${expected_identity}" ]] || return 1
  mcphub_is_managed_tunnel_pid "${pid}" || return 1
  kill -TERM "${pid}"
  wait_seconds="${MCPHUB_TUNNEL_STOP_WAIT_SECONDS:-15}"
  [[ "${wait_seconds}" =~ ^[0-9]+$ ]] || return 1
  for ((attempt = 0; attempt < wait_seconds; attempt += 1)); do
    current_identity="$(mcphub_process_identity "${pid}" 2>/dev/null || true)"
    [[ -n "${current_identity}" ]] || break
    if [[ "${current_identity}" != "${expected_identity}" ]]; then
      printf 'tunnel pid %s was reused after SIGTERM; preserving receipts\n' "${pid}" >&2
      return 1
    fi
    sleep 1
  done
  current_identity="$(mcphub_process_identity "${pid}" 2>/dev/null || true)"
  if [[ "${current_identity}" == "${expected_identity}" ]]; then
    printf 'managed tunnel pid %s did not stop after SIGTERM\n' "${pid}" >&2
    return 1
  fi
  [[ -z "${current_identity}" ]] || return 1
  if ! mcphub_managed_tunnel_process_absent; then
    printf 'managed tunnel process remains after tracked connector stopped\n' >&2
    return 1
  fi
  rm -f "${MCPHUB_TUNNEL_PID_FILE}" "${MCPHUB_TUNNEL_IDENTITY_FILE}"
  mcphub_assert_tunnel_absent
}

mcphub_start_activation_guard() {
  case "${MCPHUB_REMOTE_MODE:-disabled}" in
    disabled)
      mcphub_assert_activation_guard_absent
      return
      ;;
    capture)
      mcphub_remote_capture_ready || return 1
      ;;
    public)
      mcphub_remote_public_ready || return 1
      ;;
    *) return 1 ;;
  esac
  mcphub_tunnel_pid_running || return 1
  local receipt_digest pid identity current_identity
  receipt_digest="$(mcphub_activation_receipt_digest)" || return 1
  [[ "${receipt_digest}" =~ ^[0-9a-f]{64}$ ]] || return 1
  if mcphub_activation_guard_pid_running "${receipt_digest}"; then
    return 0
  fi
  mcphub_assert_activation_guard_absent || {
    printf 'an untracked or stale activation expiry guard exists; refusing exposure\n' >&2
    return 1
  }
  nohup bash "${MCPHUB_ACTIVATION_GUARD_SCRIPT}" \
    --receipt "${MCPHUB_REMOTE_ACTIVATION_RECEIPT_PATH}" \
    --receipt-sha256 "${receipt_digest}" </dev/null >>"${MCPHUB_ACTIVATION_GUARD_LOG_FILE}" 2>&1 &
  pid="$!"
  identity="$(mcphub_process_identity "${pid}" 2>/dev/null || true)"
  if [[ -z "${identity}" ]] || ! mcphub_is_activation_guard_pid "${pid}" "${receipt_digest}"; then
    [[ -z "${identity}" ]] || kill -TERM "${pid}" >/dev/null 2>&1 || true
    printf 'activation expiry guard process identity could not be verified\n' >&2
    return 1
  fi
  if ! mcphub_write_private_text "${MCPHUB_ACTIVATION_GUARD_PID_FILE}" "${pid}" \
    || ! mcphub_write_private_text "${MCPHUB_ACTIVATION_GUARD_IDENTITY_FILE}" "${identity}" \
    || ! mcphub_activation_guard_pid_running "${receipt_digest}"; then
    current_identity="$(mcphub_process_identity "${pid}" 2>/dev/null || true)"
    if [[ "${current_identity}" == "${identity}" ]] && mcphub_is_activation_guard_pid "${pid}" "${receipt_digest}"; then
      kill -TERM "${pid}" >/dev/null 2>&1 || true
    fi
    rm -f "${MCPHUB_ACTIVATION_GUARD_PID_FILE}" "${MCPHUB_ACTIVATION_GUARD_IDENTITY_FILE}"
    printf 'activation expiry guard identity receipt publication failed\n' >&2
    return 1
  fi
}

mcphub_stop_activation_guard() {
  local pid expected_identity current_identity attempt wait_seconds
  if [[ -e "${MCPHUB_ACTIVATION_GUARD_PID_FILE}" || -L "${MCPHUB_ACTIVATION_GUARD_PID_FILE}" ]]; then
    [[ -f "${MCPHUB_ACTIVATION_GUARD_PID_FILE}" \
      && ! -L "${MCPHUB_ACTIVATION_GUARD_PID_FILE}" \
      && -O "${MCPHUB_ACTIVATION_GUARD_PID_FILE}" \
      && "$(mcphub_private_file_mode "${MCPHUB_ACTIVATION_GUARD_PID_FILE}")" == "600" ]] || {
      printf 'activation guard pid receipt ownership or mode is invalid\n' >&2
      return 1
    }
  fi
  pid="$(mcphub_read_pid_file "${MCPHUB_ACTIVATION_GUARD_PID_FILE}" 2>/dev/null || true)"
  if [[ -z "${pid}" ]]; then
    if ! mcphub_managed_activation_guard_process_absent; then
      printf 'activation guard is present without a valid pid receipt\n' >&2
      return 1
    fi
    rm -f "${MCPHUB_ACTIVATION_GUARD_PID_FILE}" "${MCPHUB_ACTIVATION_GUARD_IDENTITY_FILE}"
    mcphub_assert_activation_guard_absent
    return
  fi
  if ! mcphub_activation_guard_pid_running; then
    current_identity="$(mcphub_process_identity "${pid}" 2>/dev/null || true)"
    if [[ -n "${current_identity}" ]]; then
      printf 'refusing to stop activation guard pid %s without an exact identity receipt\n' "${pid}" >&2
      return 1
    fi
    if ! mcphub_managed_activation_guard_process_absent; then
      printf 'activation guard remains after its tracked pid exited\n' >&2
      return 1
    fi
    rm -f "${MCPHUB_ACTIVATION_GUARD_PID_FILE}" "${MCPHUB_ACTIVATION_GUARD_IDENTITY_FILE}"
    mcphub_assert_activation_guard_absent
    return
  fi
  expected_identity="$(cat "${MCPHUB_ACTIVATION_GUARD_IDENTITY_FILE}")"
  current_identity="$(mcphub_process_identity "${pid}")" || return 1
  [[ "${current_identity}" == "${expected_identity}" ]] || return 1
  mcphub_is_activation_guard_pid "${pid}" || return 1
  kill -TERM "${pid}"
  wait_seconds="${MCPHUB_ACTIVATION_GUARD_STOP_WAIT_SECONDS:-15}"
  [[ "${wait_seconds}" =~ ^[0-9]+$ ]] || return 1
  for ((attempt = 0; attempt < wait_seconds; attempt += 1)); do
    current_identity="$(mcphub_process_identity "${pid}" 2>/dev/null || true)"
    [[ -n "${current_identity}" ]] || break
    if [[ "${current_identity}" != "${expected_identity}" ]]; then
      printf 'activation guard pid %s was reused after SIGTERM; preserving receipts\n' "${pid}" >&2
      return 1
    fi
    sleep 1
  done
  current_identity="$(mcphub_process_identity "${pid}" 2>/dev/null || true)"
  if [[ "${current_identity}" == "${expected_identity}" ]]; then
    printf 'activation guard pid %s did not stop after SIGTERM\n' "${pid}" >&2
    return 1
  fi
  [[ -z "${current_identity}" ]] || return 1
  if ! mcphub_managed_activation_guard_process_absent; then
    printf 'managed activation guard remains after tracked guard stopped\n' >&2
    return 1
  fi
  rm -f "${MCPHUB_ACTIVATION_GUARD_PID_FILE}" "${MCPHUB_ACTIVATION_GUARD_IDENTITY_FILE}"
  mcphub_assert_activation_guard_absent
}

mcphub_release_activation_guard_receipts() {
  local pid expected_identity current_identity
  pid="$(mcphub_read_pid_file "${MCPHUB_ACTIVATION_GUARD_PID_FILE}" 2>/dev/null || true)"
  [[ "${pid}" == "${BASHPID:-$$}" ]] || return 0
  [[ -f "${MCPHUB_ACTIVATION_GUARD_IDENTITY_FILE}" \
    && ! -L "${MCPHUB_ACTIVATION_GUARD_IDENTITY_FILE}" \
    && -O "${MCPHUB_ACTIVATION_GUARD_IDENTITY_FILE}" ]] || return 1
  expected_identity="$(cat "${MCPHUB_ACTIVATION_GUARD_IDENTITY_FILE}")"
  current_identity="$(mcphub_process_identity "${pid}" 2>/dev/null || true)"
  [[ -n "${expected_identity}" && "${current_identity}" == "${expected_identity}" ]] || return 1
  mcphub_is_activation_guard_pid "${pid}" || return 1
  rm -f "${MCPHUB_ACTIVATION_GUARD_PID_FILE}" "${MCPHUB_ACTIVATION_GUARD_IDENTITY_FILE}"
}

mcphub_reconcile_remote_exposure() {
  case "${MCPHUB_REMOTE_MODE:-disabled}" in
    disabled)
      mcphub_stop_tunnel
      mcphub_assert_tunnel_absent
      mcphub_stop_activation_guard
      mcphub_assert_activation_guard_absent
      ;;
    capture|public)
      mcphub_start_tunnel
      mcphub_start_activation_guard
      ;;
    *) return 1 ;;
  esac
}

mcphub_start_local() {
  local tracked_pid tracked_identity current_pid current_identity stop_status
  mcphub_prepare_run_directory
  if mcphub_runtime_is_mode_ready; then
    return 0
  fi
  if ! mcphub_distribution_is_selected; then
    printf 'no verified content-addressed MCPHub downstream is selected\n' >&2
    return 1
  fi
  if mcphub_launch_agent_loaded; then
    printf 'MCPHub LaunchAgent is loaded; waiting for its selected runtime\n' >&2
    mcphub_wait_runtime_after_start
    return
  fi
  if ! mcphub_acquire_instance_lock; then
    printf 'MCPHub instance lock is held; waiting for the selected runtime\n' >&2
    mcphub_wait_runtime_after_start
    return
  fi
  if mcphub_pid_file_running "${MCPHUB_PID_FILE}"; then
    tracked_pid="$(mcphub_read_pid_file "${MCPHUB_PID_FILE}")" || {
      mcphub_release_instance_lock
      return 1
    }
    tracked_identity="$(mcphub_managed_local_identity "${tracked_pid}" 2>/dev/null || true)"
    if [[ -z "${tracked_identity}" ]]; then
      printf 'refusing to replace unmanaged MCPHub pid %s\n' "${tracked_pid}" >&2
      mcphub_release_instance_lock
      return 1
    fi
    if mcphub_runtime_is_ready; then
      printf 'tracked MCPHub pid %s is healthy in another remote mode; replacing it safely\n' "${tracked_pid}" >&2
    else
      printf 'tracked MCPHub pid %s is starting; waiting before replacement\n' "${tracked_pid}" >&2
      if mcphub_wait_runtime_after_start; then
        mcphub_release_instance_lock
        return 0
      fi
    fi
    current_pid="$(mcphub_read_pid_file "${MCPHUB_PID_FILE}" 2>/dev/null || true)"
    current_identity="$(mcphub_process_identity "${current_pid}" 2>/dev/null || true)"
    if [[ "${current_pid}" != "${tracked_pid}" || "${current_identity}" != "${tracked_identity}" ]]; then
      printf 'MCPHub pid receipt or process identity changed while waiting; refusing replacement\n' >&2
      mcphub_release_instance_lock
      return 1
    fi
    if mcphub_stop_managed_local "${tracked_identity}" true; then
      :
    else
      stop_status=$?
      if [[ "${stop_status}" -eq 2 ]]; then
        mcphub_release_instance_lock
        return 0
      fi
      mcphub_release_instance_lock
      return 1
    fi
  fi
  printf 'starting selected MCPHub downstream on 127.0.0.1:46683; logs: %s\n' "${MCPHUB_LOG_FILE}" >&2
  (
    cd "${MCPHUB_REPO_ROOT}"
    exec nohup bash "${MCPHUB_SCRIPT_DIR}/start-server.sh" </dev/null
  ) >>"${MCPHUB_LOG_FILE}" 2>&1 &
  printf '%s\n' "$!" >"${MCPHUB_PID_FILE}"
  if mcphub_wait_runtime_after_start; then
    mcphub_release_instance_lock
    return 0
  fi
  mcphub_release_instance_lock
  return 1
}
