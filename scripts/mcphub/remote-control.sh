#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

usage() {
  cat <<'EOF'
Usage:
  remote-control.sh capture [--ttl-seconds SECONDS]
  remote-control.sh activate-public --registration-mode cimd|dcr \
    --observed-wire-evidence /absolute/path [--ttl-seconds SECONDS]
  remote-control.sh deactivate [--stop-all]
  remote-control.sh rollback --selection-receipt /absolute/path

All transitions stop and verify absence of the identity-bound Cloudflare tunnel
before changing the local runtime or a downstream selection. Capture starts a
short-lived, receipt-bound 46684-only tunnel whose runtime exposes immutable
OAuth discovery while MCP tool dispatch remains disabled. An identity-bound
guard tears capture and public exposure down when the receipt expires or drifts.
Public activation additionally binds OAuth policy/login inputs, semantically
validated observed-wire evidence, and conformance.
EOF
}

operation="${1:-}"
[[ -n "${operation}" ]] || {
  usage >&2
  exit 2
}
shift

ttl_seconds=""
registration_mode=""
observed_wire_evidence=""
selection_receipt=""
stop_all=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --ttl-seconds|--registration-mode|--observed-wire-evidence|--selection-receipt)
      [[ $# -ge 2 ]] || {
        printf 'missing value for %s\n' "$1" >&2
        exit 2
      }
      case "$1" in
        --ttl-seconds) ttl_seconds="$2" ;;
        --registration-mode) registration_mode="$2" ;;
        --observed-wire-evidence) observed_wire_evidence="$2" ;;
        --selection-receipt) selection_receipt="$2" ;;
      esac
      shift 2
      ;;
    --stop-all)
      stop_all=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf 'unknown argument: %s\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

mcphub_load_env

stop_tunnel_first() {
  mcphub_stop_tunnel
  if ! mcphub_assert_tunnel_absent; then
    printf 'Cloudflare tunnel absence could not be proven; transition is blocked\n' >&2
    return 1
  fi
}

stop_runtime_for_transition() {
  if mcphub_launch_agent_loaded; then
    mcphub_bootout_launch_agent
  fi
  mcphub_stop_managed_local
  if ! mcphub_listener_is_absent "${PORT}" || ! mcphub_listener_is_absent "${MCPHUB_REMOTE_PORT}"; then
    printf 'an MCPHub listener remains after the identity-verified stop; transition is blocked\n' >&2
    return 1
  fi
}

stop_guard_after_tunnel() {
  mcphub_stop_activation_guard
  if ! mcphub_assert_activation_guard_absent; then
    printf 'activation expiry guard absence could not be proven; transition is blocked\n' >&2
    return 1
  fi
}

revoke_activation_receipt() {
  node "${MCPHUB_REMOTE_ACTIVATION_HELPER}" revoke \
    --receipt "${MCPHUB_REMOTE_ACTIVATION_RECEIPT_PATH}" >/dev/null
}

issue_activation_receipt() {
  local mode="$1" ttl="$2"
  shift 2
  local -a arguments=(
    issue
    --mode "${mode}"
    --ttl-seconds "${ttl}"
    --receipt "${MCPHUB_REMOTE_ACTIVATION_RECEIPT_PATH}"
    --runtime-root "${MCPHUB_DOWNSTREAM_RUNTIME_ROOT}"
    --settings "${MCPHUB_SETTING_PATH}"
    --cloudflared-config "${MCPHUB_TUNNEL_RUNTIME_CONFIG}"
    --tunnel-name "${MCPHUB_TUNNEL_NAME:-}"
    --credentials-file "${MCPHUB_TUNNEL_CREDENTIALS_FILE:-}"
    --conformance-result "${MCPHUB_REMOTE_CONFORMANCE_RESULT_PATH}"
    --capture-receipt "${MCPHUB_REMOTE_CAPTURE_RECEIPT_PATH}"
    "$@"
  )
  node "${MCPHUB_REMOTE_ACTIVATION_HELPER}" "${arguments[@]}"
}

snapshot_capture_receipt() {
  node "${MCPHUB_REMOTE_ACTIVATION_HELPER}" snapshot-capture \
    --receipt "${MCPHUB_REMOTE_ACTIVATION_RECEIPT_PATH}" \
    --output "${MCPHUB_REMOTE_CAPTURE_RECEIPT_PATH}" \
    --runtime-root "${MCPHUB_DOWNSTREAM_RUNTIME_ROOT}" \
    --settings "${MCPHUB_SETTING_PATH}" \
    --cloudflared-config "${MCPHUB_TUNNEL_RUNTIME_CONFIG}" \
    --conformance-result "${MCPHUB_REMOTE_CONFORMANCE_RESULT_PATH}" >/dev/null
}

remaining_capture_ttl_seconds() {
  python3 -c '
import json, sys, time
receipt = json.load(open(sys.argv[1], encoding="utf-8"))
remaining = int((receipt["expiresAt"] - time.time() * 1000) // 1000)
if remaining < 60:
    raise SystemExit(1)
print(min(remaining, 1800))
' "${MCPHUB_REMOTE_ACTIVATION_RECEIPT_PATH}"
}

rebind_capture_receipt_after_runtime() {
  [[ "${MCPHUB_REMOTE_MODE}" == "capture" ]] || return 0
  chmod 600 "${MCPHUB_SETTING_PATH}" 2>/dev/null || true
  if [[ "$(mcphub_remote_activation_mode 2>/dev/null)" == "capture" ]]; then
    return 0
  fi
  printf 'runtime settings drifted after MCPHub start; rebinding the capture receipt\n' >&2
  local remaining
  remaining="$(remaining_capture_ttl_seconds)" || {
    printf 'capture receipt cannot be rebound; remaining TTL is too short or unreadable\n' >&2
    return 1
  }
  revoke_capture_receipt_snapshot
  revoke_activation_receipt
  issue_activation_receipt capture "${remaining}" >/dev/null
  snapshot_capture_receipt
}

revoke_capture_receipt_snapshot() {
  node "${MCPHUB_REMOTE_ACTIVATION_HELPER}" revoke \
    --receipt "${MCPHUB_REMOTE_CAPTURE_RECEIPT_PATH}" >/dev/null
}

prepare_activation() {
  local target_mode="$1" current_mode=""
  if [[ "${target_mode}" == "capture" \
    && ( -e "${MCPHUB_REMOTE_CAPTURE_RECEIPT_PATH}" || -L "${MCPHUB_REMOTE_CAPTURE_RECEIPT_PATH}" ) ]]; then
    printf 'a capture receipt snapshot already exists; deactivate before starting a new capture\n' >&2
    return 2
  fi
  if [[ -e "${MCPHUB_REMOTE_ACTIVATION_RECEIPT_PATH}" \
    || -L "${MCPHUB_REMOTE_ACTIVATION_RECEIPT_PATH}" ]]; then
    current_mode="$(mcphub_remote_activation_mode 2>/dev/null || true)"
    if [[ "${target_mode}" != "public" || "${current_mode}" != "capture" ]]; then
      printf 'an activation receipt already exists; run deactivate before issuing another\n' >&2
      return 2
    fi
    [[ -f "${MCPHUB_REMOTE_CAPTURE_RECEIPT_PATH}" \
      && ! -L "${MCPHUB_REMOTE_CAPTURE_RECEIPT_PATH}" ]] || {
      printf 'capture-to-public transition is missing its identity-bound receipt snapshot\n' >&2
      return 2
    }
  fi
  stop_tunnel_first
  stop_guard_after_tunnel
  stop_runtime_for_transition
  if [[ "${current_mode}" == "capture" ]]; then
    revoke_activation_receipt
  fi
  mcphub_distribution_is_selected || {
    printf 'no verified content-addressed downstream is selected\n' >&2
    return 1
  }
  "${SCRIPT_DIR}/validate-settings.sh" >/dev/null
  chmod 600 "${MCPHUB_REMOTE_CONFORMANCE_RESULT_PATH}" 2>/dev/null || {
    printf 'MCPHub conformance receipt is not owner-only mode 0600\n' >&2
    return 1
  }
  mcphub_generate_cloudflared_config >/dev/null
  mcphub_verify_cloudflared_config
}

fail_activation_closed() {
  local failure_status="$1"
  mcphub_stop_tunnel >/dev/null 2>&1 || true
  if mcphub_assert_tunnel_absent; then
    mcphub_stop_activation_guard >/dev/null 2>&1 || true
  fi
  if mcphub_assert_tunnel_absent && mcphub_assert_activation_guard_absent; then
    mcphub_stop_managed_local >/dev/null 2>&1 || true
  fi
  if mcphub_assert_tunnel_absent \
    && mcphub_assert_activation_guard_absent \
    && mcphub_listener_is_absent "${PORT}" \
    && mcphub_listener_is_absent "${MCPHUB_REMOTE_PORT}"; then
    revoke_activation_receipt >/dev/null 2>&1 || true
    if [[ "${operation}" == "capture" ]]; then
      revoke_capture_receipt_snapshot >/dev/null 2>&1 || true
    fi
    MCPHUB_REMOTE_MODE_OVERRIDE=disabled MCPHUB_TUNNEL_ENABLED=false \
      bash "${SCRIPT_DIR}/start-local-only.sh" >/dev/null 2>&1 || true
  fi
  return "${failure_status}"
}

case "${operation}" in
  capture)
    [[ -z "${registration_mode}" && -z "${observed_wire_evidence}" \
      && -z "${selection_receipt}" && "${stop_all}" == "false" ]] || {
      printf 'capture accepts only --ttl-seconds\n' >&2
      exit 2
    }
    ttl_seconds="${ttl_seconds:-1800}"
    MCPHUB_REMOTE_MODE=capture
    export MCPHUB_REMOTE_MODE
    prepare_activation capture || {
      failure_status=$?
      [[ "${failure_status}" -ne 2 ]] || exit "${failure_status}"
      fail_activation_closed "${failure_status}" || true
      exit "${failure_status}"
    }
    issue_activation_receipt capture "${ttl_seconds}" >/dev/null || {
      failure_status=$?
      fail_activation_closed "${failure_status}" || true
      exit "${failure_status}"
    }
    snapshot_capture_receipt || {
      failure_status=$?
      fail_activation_closed "${failure_status}" || true
      exit "${failure_status}"
    }
    mcphub_resolve_remote_mode || {
      failure_status=$?
      fail_activation_closed "${failure_status}" || true
      exit "${failure_status}"
    }
    if mcphub_start_local \
      && rebind_capture_receipt_after_runtime \
      && mcphub_wait_ready \
      && mcphub_wait_remote_ready capture \
      && mcphub_start_tunnel \
      && mcphub_start_activation_guard; then
      :
    else
      failure_status=$?
      fail_activation_closed "${failure_status}" || true
      exit "${failure_status}"
    fi
    mcphub_tunnel_pid_running
    mcphub_activation_guard_pid_running "$(mcphub_activation_receipt_digest)"
    printf 'restricted capture ready at https://mcp.w4w.dev/mcp/things; tool dispatch is disabled and expiry is guarded\n'
    ;;
  activate-public)
    [[ -z "${selection_receipt}" && "${stop_all}" == "false" ]] || {
      printf 'activate-public does not accept rollback/deactivation arguments\n' >&2
      exit 2
    }
    [[ "${registration_mode}" == "cimd" || "${registration_mode}" == "dcr" ]] || {
      printf 'activate-public requires --registration-mode cimd or dcr\n' >&2
      exit 2
    }
    [[ "${observed_wire_evidence}" == /* ]] || {
      printf 'activate-public requires an absolute --observed-wire-evidence path\n' >&2
      exit 2
    }
    [[ -n "${MCPHUB_OAUTH_POLICY_PATH:-}" && -n "${MCPHUB_OAUTH_LOGIN_CREDENTIAL_PATH:-}" ]] || {
      printf 'MCPHUB_OAUTH_POLICY_PATH and MCPHUB_OAUTH_LOGIN_CREDENTIAL_PATH are required\n' >&2
      exit 1
    }
    # Final evidence is fresh for at most 24 hours from capture, so leave one
    # hour of headroom for the capture-to-public transition by default.
    ttl_seconds="${ttl_seconds:-82800}"
    MCPHUB_REMOTE_MODE=public
    MCPHUB_REMOTE_OBSERVED_WIRE_EVIDENCE_PATH="${observed_wire_evidence}"
    export MCPHUB_REMOTE_MODE MCPHUB_REMOTE_OBSERVED_WIRE_EVIDENCE_PATH
    prepare_activation public || {
      failure_status=$?
      [[ "${failure_status}" -ne 2 ]] || exit "${failure_status}"
      fail_activation_closed "${failure_status}" || true
      exit "${failure_status}"
    }
    issue_activation_receipt public "${ttl_seconds}" \
      --registration-mode "${registration_mode}" \
      --oauth-policy "${MCPHUB_OAUTH_POLICY_PATH}" \
      --oauth-login-credential "${MCPHUB_OAUTH_LOGIN_CREDENTIAL_PATH}" \
      --observed-wire-evidence "${observed_wire_evidence}" >/dev/null || {
      failure_status=$?
      fail_activation_closed "${failure_status}" || true
      exit "${failure_status}"
    }
    mcphub_resolve_remote_mode || {
      failure_status=$?
      fail_activation_closed "${failure_status}" || true
      exit "${failure_status}"
    }
    if mcphub_start_local \
      && mcphub_wait_ready \
      && mcphub_wait_remote_ready public \
      && mcphub_start_tunnel \
      && mcphub_start_activation_guard; then
      :
    else
      failure_status=$?
      fail_activation_closed "${failure_status}" || true
      exit "${failure_status}"
    fi
    mcphub_tunnel_pid_running
    mcphub_activation_guard_pid_running "$(mcphub_activation_receipt_digest)"
    printf 'public activation ready at https://mcp.w4w.dev/mcp/things through the 46684-only ingress\n'
    ;;
  deactivate)
    [[ -z "${ttl_seconds}" && -z "${registration_mode}" && -z "${observed_wire_evidence}" \
      && -z "${selection_receipt}" ]] || {
      printf 'deactivate accepts only --stop-all\n' >&2
      exit 2
    }
    stop_tunnel_first
    stop_guard_after_tunnel
    stop_runtime_for_transition
    revoke_activation_receipt
    revoke_capture_receipt_snapshot
    if [[ "${stop_all}" == "false" ]]; then
      MCPHUB_REMOTE_MODE_OVERRIDE=disabled MCPHUB_TUNNEL_ENABLED=false \
        bash "${SCRIPT_DIR}/start-local-only.sh"
    fi
    printf 'remote activation deactivated; Cloudflare absence verified\n'
    ;;
  rollback)
    [[ -z "${ttl_seconds}" && -z "${registration_mode}" && -z "${observed_wire_evidence}" \
      && "${stop_all}" == "false" && "${selection_receipt}" == /* ]] || {
      printf 'rollback requires only --selection-receipt /absolute/path\n' >&2
      exit 2
    }
    stop_tunnel_first
    stop_guard_after_tunnel
    stop_runtime_for_transition
    revoke_activation_receipt
    revoke_capture_receipt_snapshot
    node "${SCRIPT_DIR}/downstream-select.mjs" rollback \
      --runtime-root "${MCPHUB_DOWNSTREAM_RUNTIME_ROOT}" \
      --receipt "${selection_receipt}"
    MCPHUB_REMOTE_MODE_OVERRIDE=disabled MCPHUB_TUNNEL_ENABLED=false \
      bash "${SCRIPT_DIR}/start-local-only.sh"
    printf 'downstream rollback completed after verified Cloudflare teardown\n'
    ;;
  *)
    printf 'unknown operation: %s\n' "${operation}" >&2
    usage >&2
    exit 2
    ;;
esac
