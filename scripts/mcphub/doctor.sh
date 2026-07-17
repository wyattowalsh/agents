#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

mcphub_load_env
doctor_status=0

printf 'settings: '
"${SCRIPT_DIR}/validate-settings.sh" >/dev/null
printf 'ok\n'

printf 'node: '
if command -v node >/dev/null 2>&1 && command -v npx >/dev/null 2>&1; then
  printf 'available\n'
else
  printf 'missing node or npx\n'
fi

printf 'health: '
health_body="$(curl -fsS --max-time 2 "$(mcphub_health_url)" 2>/dev/null || true)"
if [[ -n "${health_body}" ]]; then
  health_status="$(printf '%s' "${health_body}" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("status","unknown"))' 2>/dev/null || printf 'unknown')"
  case "${health_status}" in
    healthy)
      printf 'healthy\n'
      ;;
    degraded)
      connected="$(printf '%s' "${health_body}" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("connected","?"))' 2>/dev/null || printf '?')"
      total="$(printf '%s' "${health_body}" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("total","?"))' 2>/dev/null || printf '?')"
      printf 'degraded (%s/%s servers connected)\n' "${connected}" "${total}"
      ;;
    unhealthy)
      printf 'unhealthy\n'
      ;;
    *)
      if mcphub_is_healthy; then
        printf 'healthy (legacy response)\n'
      else
        printf 'not running\n'
      fi
      ;;
  esac
else
  if mcphub_is_healthy; then
    printf 'healthy\n'
  else
    printf 'not running\n'
  fi
fi

printf 'listener: '
if command -v lsof >/dev/null 2>&1 && lsof -nP -iTCP:"${PORT}" -sTCP:LISTEN >/dev/null 2>&1; then
  if mcphub_listener_is_loopback; then
    printf 'loopback-only on %s:%s\n' "${MCPHUB_BIND_HOST}" "${PORT}"
  else
    printf 'unsafe non-loopback listener on %s (%s)\n' "${PORT}" "$(mcphub_listener_endpoints | paste -sd, -)"
    doctor_status=1
  fi
else
  printf 'not listening on %s\n' "${PORT}"
fi

printf 'wrapper pid: '
if mcphub_pid_running; then
  pid="$(mcphub_read_pid_file "${MCPHUB_PID_FILE}" 2>/dev/null || true)"
  if mcphub_pid_file_managed_running "${MCPHUB_PID_FILE}"; then
    printf 'managed-running (%s)\n' "${pid}"
  else
    if [[ -n "${pid}" ]]; then
      printf 'running-unmanaged (%s)\n' "${pid}"
    else
      printf 'invalid\n'
    fi
  fi
else
  printf 'absent\n'
fi

printf 'child pid: '
if mcphub_pid_file_running "${MCPHUB_CHILD_PID_FILE}"; then
  child_pid="$(mcphub_read_pid_file "${MCPHUB_CHILD_PID_FILE}" 2>/dev/null || true)"
  if [[ -n "${child_pid}" ]] && mcphub_is_managed_local_pid "${child_pid}"; then
    printf 'managed-running (%s)\n' "${child_pid}"
  elif [[ -n "${child_pid}" ]]; then
    printf 'running-unmanaged (%s)\n' "${child_pid}"
  else
    printf 'invalid\n'
  fi
else
  printf 'absent\n'
fi

if ! mcphub_is_healthy && { mcphub_pid_running || mcphub_pid_file_running "${MCPHUB_CHILD_PID_FILE}"; }; then
  printf 'state: stale-or-wedged pid present while health check fails\n'
fi

printf 'MCPHUB_BEARER_TOKEN: '
if [[ -n "${MCPHUB_BEARER_TOKEN:-}" && "${MCPHUB_BEARER_TOKEN}" != replace-with-local-* ]]; then
  printf 'set\n'
else
  printf 'missing\n'
fi

printf 'MCPHub tunnel: '
if mcphub_tunnel_enabled; then
  if mcphub_pid_file_running "${MCPHUB_TUNNEL_PID_FILE}"; then
    printf 'enabled and running'
  else
    printf 'enabled but not running'
  fi
  if [[ -n "${MCPHUB_PUBLIC_URL:-}" ]]; then
    printf ' (%s)' "${MCPHUB_PUBLIC_URL}"
  fi
  printf '\n'
else
  printf 'disabled\n'
fi

printf 'Zapier handoff: '
if [[ -n "${MCPHUB_ZAPIER_WEBHOOK_URL:-}" ]]; then
  printf 'configured\n'
else
  printf 'not configured\n'
fi

printf 'SMART_ROUTING_ENABLED: %s\n' "${SMART_ROUTING_ENABLED:-false}"
printf 'Local exposure note: UI, health, and OAuth metadata may be public; loopback-only binding is required.\n'

launcher="${SCRIPT_DIR}/package-version-check-mcp.sh"
printf 'package-version-check-mcp launcher: '
if [[ -x "${launcher}" ]]; then
  start_ms="$(python3 -c 'import time; print(int(time.time()*1000))')"
  if "${launcher}" --help >/dev/null 2>&1; then
    end_ms="$(python3 -c 'import time; print(int(time.time()*1000))')"
    elapsed="$((end_ms - start_ms))"
    printf 'ok (%ss)\n' "$((elapsed / 1000))"
  else
    printf 'present but --help failed\n'
  fi
else
  printf 'missing or not executable\n'
fi

exit "${doctor_status}"
