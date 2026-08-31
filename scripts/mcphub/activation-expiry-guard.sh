#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

usage() {
  printf 'usage: activation-expiry-guard.sh --receipt /absolute/path --receipt-sha256 64hex\n'
}

receipt=""
receipt_sha256=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --receipt)
      [[ $# -ge 2 ]] || {
        usage >&2
        exit 2
      }
      receipt="$2"
      shift 2
      ;;
    --receipt-sha256)
      [[ $# -ge 2 ]] || {
        usage >&2
        exit 2
      }
      receipt_sha256="$2"
      shift 2
      ;;
    *)
      usage >&2
      exit 2
      ;;
  esac
done

[[ "${receipt}" == /* && "${receipt_sha256}" =~ ^[0-9a-f]{64}$ ]] || {
  usage >&2
  exit 2
}

mcphub_load_env
[[ "${receipt}" == "${MCPHUB_REMOTE_ACTIVATION_RECEIPT_PATH}" ]] || {
  printf 'activation guard receipt path does not match the configured identity\n' >&2
  exit 1
}

release_guard_receipts() {
  mcphub_release_activation_guard_receipts >/dev/null 2>&1 || true
}
trap release_guard_receipts EXIT
trap 'exit 0' INT TERM

poll_seconds="${MCPHUB_ACTIVATION_GUARD_POLL_SECONDS:-2}"
[[ "${poll_seconds}" =~ ^[1-9]$|^[12][0-9]$|^30$ ]] || {
  printf 'activation guard poll interval must be 1-30 seconds\n' >&2
  exit 1
}

guard_mode="$(mcphub_remote_activation_mode 2>/dev/null || true)"
[[ "${guard_mode}" == "capture" || "${guard_mode}" == "public" ]] || {
  printf 'activation guard did not receive a valid capture or public receipt\n' >&2
  exit 1
}

receipt_is_current_and_valid() {
  local current_digest mode
  current_digest="$(mcphub_activation_receipt_digest 2>/dev/null || true)"
  [[ "${current_digest}" == "${receipt_sha256}" ]] || return 1
  # Poll identity + expiry only. Live runtime settings include OAuth/session
  # collections that MCPHub rewrites after start; re-hashing that file every
  # interval falsely tears down an otherwise valid capture/public tunnel.
  mode="$(mcphub_activation_receipt_unexpired "${guard_mode}" 2>/dev/null || true)"
  [[ "${mode}" == "${guard_mode}" ]]
}

while receipt_is_current_and_valid; do
  sleep "${poll_seconds}"
done

printf 'activation receipt expired or drifted; tearing down remote exposure\n' >&2
mcphub_stop_tunnel
mcphub_assert_tunnel_absent

if mcphub_launch_agent_loaded; then
  mcphub_bootout_launch_agent
fi
if mcphub_pid_file_running "${MCPHUB_PID_FILE}"; then
  mcphub_stop_managed_local
else
  rm -f "${MCPHUB_PID_FILE}"
fi
mcphub_listener_is_absent "${PORT}"
mcphub_listener_is_absent "${MCPHUB_REMOTE_PORT}"

current_digest="$(mcphub_activation_receipt_digest 2>/dev/null || true)"
if [[ "${current_digest}" == "${receipt_sha256}" ]]; then
  node "${MCPHUB_REMOTE_ACTIVATION_HELPER}" revoke \
    --receipt "${MCPHUB_REMOTE_ACTIVATION_RECEIPT_PATH}" \
    --expected-sha256 "${receipt_sha256}" >/dev/null
fi
if [[ "${guard_mode}" == "capture" ]]; then
  node "${MCPHUB_REMOTE_ACTIVATION_HELPER}" revoke \
    --receipt "${MCPHUB_REMOTE_CAPTURE_RECEIPT_PATH}" \
    --expected-sha256 "${receipt_sha256}" >/dev/null
else
  node "${MCPHUB_REMOTE_ACTIVATION_HELPER}" revoke \
    --receipt "${MCPHUB_REMOTE_CAPTURE_RECEIPT_PATH}" >/dev/null
fi

export MCPHUB_REMOTE_MODE_OVERRIDE=disabled
export MCPHUB_REMOTE_MODE=disabled
export MCPHUB_TUNNEL_ENABLED=false
mcphub_start_local
mcphub_wait_mode_ready
mcphub_listener_is_absent "${MCPHUB_REMOTE_PORT}"
printf 'expired remote exposure removed; local-only MCPHub restored\n' >&2
