# Optional hook validation.
# shellcheck shell=bash

hooks_validate() {
  local label
  if [ -z "${AGENTS_ROOT}" ]; then
    record_phase "hooks" "skip" "no-agents-root"
    mark_skip
    return 0
  fi
  if ! _wagents_available; then
    record_phase "hooks" "skip" "wagents-missing"
    mark_skip
    return 0
  fi
  if [ "${APPLY:-0}" -ne 1 ] && [ "${CHECK:-0}" -ne 1 ]; then
    label="$(_wagents_label)"
    log_info "Would run: ${label} hooks validate --format json"
    record_phase "hooks" "skip" "dry-run"
    mark_skip
    return 0
  fi
  if run_wagents hooks validate --format json >/dev/null; then
    record_phase "hooks" "ok" "validated"
    mark_run
    return 0
  fi
  log_warn "Hook validation reported issues."
  record_phase "hooks" "warn" "validate-failed"
  return 0
}
