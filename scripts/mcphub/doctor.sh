#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

mcphub_cloudflared_process_state() {
  if ! command -v pgrep >/dev/null 2>&1; then
    printf 'inspection-unavailable\n'
    return 2
  fi

  local pids="" pgrep_status=0 pid managed=0 unmanaged=0
  if pids="$(pgrep -x cloudflared 2>/dev/null)"; then
    pgrep_status=0
  else
    pgrep_status=$?
  fi
  if [[ "${pgrep_status}" -eq 1 && -z "${pids}" ]]; then
    printf 'absent\n'
    return 0
  fi
  if [[ "${pgrep_status}" -ne 0 || -z "${pids}" ]]; then
    printf 'inspection-failed\n'
    return 2
  fi

  while IFS= read -r pid; do
    if [[ ! "${pid}" =~ ^[0-9]+$ ]]; then
      printf 'inspection-failed\n'
      return 2
    fi
    if mcphub_is_managed_tunnel_pid "${pid}"; then
      managed=1
    else
      unmanaged=1
    fi
  done <<<"${pids}"

  if [[ "${managed}" -eq 1 && "${unmanaged}" -eq 1 ]]; then
    printf 'managed-and-unmanaged-present\n'
  elif [[ "${managed}" -eq 1 ]]; then
    printf 'managed-present\n'
  else
    printf 'unmanaged-present\n'
  fi
  return 1
}

if [[ "${MCPHUB_DOCTOR_LIBRARY_ONLY:-false}" == "true" ]]; then
  return 0
fi

mcphub_load_env
doctor_status=0
if ! mcphub_resolve_remote_mode; then
  doctor_status=1
fi

printf 'settings: '
if "${SCRIPT_DIR}/validate-settings.sh" >/dev/null 2>&1; then
  printf 'valid\n'
else
  printf 'invalid\n'
  doctor_status=1
fi

printf 'node: '
if command -v node >/dev/null 2>&1; then
  printf 'available\n'
else
  printf 'missing\n'
  doctor_status=1
fi

printf 'selected distribution: '
if mcphub_distribution_is_selected; then
  printf 'verified\n'
else
  printf 'absent or invalid\n'
  doctor_status=1
fi

printf 'runtime pid: '
pid="$(mcphub_read_pid_file "${MCPHUB_PID_FILE}" 2>/dev/null || true)"
if [[ -z "${pid}" ]]; then
  printf 'absent\n'
elif mcphub_pid_file_managed_running "${MCPHUB_PID_FILE}"; then
  printf 'selected-running (%s)\n' "${pid}"
else
  printf 'unmanaged-or-stale (%s)\n' "${pid}"
  doctor_status=1
fi

printf 'local listener: '
if mcphub_listener_is_loopback "${PORT}"; then
  printf '127.0.0.1:46683\n'
else
  printf 'absent or noncanonical\n'
fi

printf 'local Things route: '
if mcphub_local_route_is_ready; then
  printf 'authenticated 405/Allow POST readiness passed\n'
elif [[ -n "${pid}" ]]; then
  printf 'not ready\n'
  doctor_status=1
else
  printf 'not running\n'
fi

printf 'remote mode: %s\n' "${MCPHUB_REMOTE_MODE}"
printf 'remote listener: '
if mcphub_listener_is_loopback "${MCPHUB_REMOTE_PORT}"; then
  if [[ "${MCPHUB_REMOTE_MODE}" == "disabled" ]]; then
    printf 'unexpected while remote mode is disabled\n'
    doctor_status=1
  else
    printf '127.0.0.1:46684\n'
  fi
else
  if [[ "${MCPHUB_REMOTE_MODE}" == "disabled" ]]; then
    printf 'disabled and absent\n'
  else
    printf 'required by mode but absent\n'
    doctor_status=1
  fi
fi

printf 'remote public readiness: '
if mcphub_remote_public_ready; then
  printf 'stamped and dispatch-enabled\n'
else
  printf 'fail-closed\n'
fi

printf 'remote activation receipt: '
activation_mode=""
if [[ -e "${MCPHUB_REMOTE_ACTIVATION_RECEIPT_PATH}" \
  || -L "${MCPHUB_REMOTE_ACTIVATION_RECEIPT_PATH}" ]]; then
  if activation_mode="$(mcphub_remote_activation_mode 2>/dev/null)"; then
    printf 'verified (%s)\n' "${activation_mode}"
    if [[ "${MCPHUB_REMOTE_MODE}" == "disabled" ]]; then
      printf 'stale remote activation receipt is present while remote mode is disabled\n' >&2
      doctor_status=1
    fi
  elif [[ "${MCPHUB_REMOTE_MODE}" == "disabled" ]]; then
    printf 'invalid (ignored; remote disabled)\n'
  else
    printf 'invalid\n'
    doctor_status=1
  fi
else
  printf 'absent\n'
  if [[ "${MCPHUB_REMOTE_MODE}" != "disabled" ]]; then
    doctor_status=1
  fi
fi

if [[ "${MCPHUB_REMOTE_MODE}" == "disabled" ]]; then
  printf 'cloudflared process: '
  cloudflared_state=""
  if cloudflared_state="$(mcphub_cloudflared_process_state)"; then
    printf '%s\n' "${cloudflared_state}"
  else
    printf '%s\n' "${cloudflared_state}"
    doctor_status=1
  fi

  printf 'tunnel pid receipt: '
  if [[ -e "${MCPHUB_TUNNEL_PID_FILE}" || -L "${MCPHUB_TUNNEL_PID_FILE}" \
    || -e "${MCPHUB_TUNNEL_IDENTITY_FILE}" || -L "${MCPHUB_TUNNEL_IDENTITY_FILE}" ]]; then
    printf 'unexpected while remote mode is disabled\n'
    doctor_status=1
  else
    printf 'absent\n'
  fi

fi

printf 'activation expiry guard: '
if [[ "${MCPHUB_REMOTE_MODE}" == "capture" || "${MCPHUB_REMOTE_MODE}" == "public" ]]; then
  receipt_digest="$(mcphub_activation_receipt_digest 2>/dev/null || true)"
  if [[ "${receipt_digest}" =~ ^[0-9a-f]{64}$ ]] \
    && mcphub_activation_guard_pid_running "${receipt_digest}"; then
    printf 'identity-bound and active\n'
  else
    printf 'missing or invalid\n'
    doctor_status=1
  fi
elif mcphub_assert_activation_guard_absent; then
  printf 'absent\n'
else
  printf 'unexpected while remote mode is disabled\n'
  doctor_status=1
fi

printf 'tunnel: '
case "${MCPHUB_REMOTE_MODE}" in
  capture)
    if mcphub_remote_capture_ready && mcphub_tunnel_pid_running; then
      printf 'restricted capture running for https://mcp.w4w.dev/mcp/things (tool dispatch disabled)\n'
    else
      printf 'capture requested but gated off\n'
      doctor_status=1
    fi
    ;;
  public)
    if mcphub_remote_public_ready && mcphub_tunnel_pid_running; then
      printf 'public and running for https://mcp.w4w.dev/mcp/things\n'
    else
      printf 'public requested but gated off\n'
      doctor_status=1
    fi
    ;;
  disabled)
    printf 'disabled\n'
    ;;
esac

printf 'MCPHUB_BEARER_TOKEN: '
if mcphub_require_token >/dev/null 2>&1; then
  printf 'set\n'
else
  printf 'missing\n'
  doctor_status=1
fi

exit "${doctor_status}"
