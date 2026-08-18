# Optional per-harness doctors.
# shellcheck shell=bash

run_optional_doctors() {
  if [ -z "${AGENTS_ROOT}" ]; then
    record_phase "doctors" "skip" "no-agents-root"
    mark_skip
    return 0
  fi
  if ! _wagents_available; then
    record_phase "doctors" "skip" "wagents-missing"
    mark_skip
    return 0
  fi
  if [ "${APPLY:-0}" -ne 1 ] && [ "${CHECK:-0}" -ne 1 ]; then
    log_info "Would run optional cursor-cli / grok doctors when those binaries exist"
    record_phase "doctors" "skip" "dry-run"
    mark_skip
    return 0
  fi
  if command -v agent >/dev/null 2>&1 || command -v cursor-agent >/dev/null 2>&1; then
    run_wagents cursor-cli doctor --format json >/dev/null || log_warn "cursor-cli doctor reported issues"
  fi
  if command -v grok >/dev/null 2>&1; then
    run_wagents grok doctor --format json >/dev/null || log_warn "grok doctor reported issues"
  fi
  record_phase "doctors" "ok" "optional"
  mark_run
}
