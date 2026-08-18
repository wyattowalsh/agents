# MCPHub settings check and optional local-only start (never tunnel).
# shellcheck shell=bash

mcphub_check_settings() {
  local script
  if [ "${SKIP_MCPHUB:-0}" -eq 1 ]; then
    record_phase "mcphub-check" "skip" "skip-mcphub"
    mark_skip
    return 0
  fi
  if [ -z "${AGENTS_ROOT}" ]; then
    record_phase "mcphub-check" "skip" "no-agents-root"
    mark_skip
    return 0
  fi
  script="${AGENTS_ROOT}/scripts/generate_mcphub_settings.py"
  if [ ! -f "$script" ] || ! command -v uv >/dev/null 2>&1; then
    record_phase "mcphub-check" "skip" "missing-uv-or-script"
    mark_skip
    return 0
  fi
  if [ "${APPLY:-0}" -ne 1 ] && [ "${CHECK:-0}" -ne 1 ]; then
    log_info "Would run: uv run python ${script} --check"
    record_phase "mcphub-check" "skip" "dry-run"
    mark_skip
    return 0
  fi
  if (cd "${AGENTS_ROOT}" && uv run python "$script" --check); then
    record_phase "mcphub-check" "ok" "in-sync"
    mark_run
    return 0
  fi
  log_warn "MCPHub settings check reported drift or failure."
  record_phase "mcphub-check" "warn" "check-failed"
  return 0
}

mcphub_start_local_if_requested() {
  local starter
  if [ "${SKIP_MCPHUB:-0}" -eq 1 ]; then
    record_phase "mcphub-start" "skip" "skip-mcphub"
    mark_skip
    return 0
  fi
  if [ "${WANT_MCPHUB:-0}" -ne 1 ]; then
    record_phase "mcphub-start" "skip" "pass --mcphub to start local hub"
    mark_skip
    return 0
  fi
  if [ -z "${AGENTS_ROOT}" ]; then
    record_phase "mcphub-start" "skip" "no-agents-root"
    mark_skip
    return 0
  fi
  starter="${AGENTS_ROOT}/scripts/mcphub/start-local-only.sh"
  if [ "${APPLY:-0}" -ne 1 ]; then
    log_info "Would start local MCPHub via ${starter} (MCPHUB_TUNNEL_ENABLED=false)"
    record_phase "mcphub-start" "skip" "dry-run-start-local-only"
    mark_skip
    return 0
  fi
  if [ ! -x "$starter" ]; then
    log_warn "Missing ${starter}"
    record_phase "mcphub-start" "skip" "starter-missing"
    mark_skip
    return 0
  fi
  if MCPHUB_TUNNEL_ENABLED=false "$starter"; then
    record_phase "mcphub-start" "ok" "local-only"
    mark_run
    return 0
  fi
  log_warn "Local MCPHub did not become healthy."
  record_phase "mcphub-start" "warn" "unhealthy"
  return 0
}
