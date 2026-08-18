# Skills preview (always dry-run) and optional live apply.
# shellcheck shell=bash

skills_preview() {
  local label
  local -a extra=()
  local id
  if [ -z "${HARNESS_IDS}" ]; then
    log_info "No harnesses detected; skipping skills preview."
    record_phase "skills-preview" "skip" "no-harnesses"
    mark_skip
    return 0
  fi
  if [ -z "${AGENTS_ROOT}" ]; then
    record_phase "skills-preview" "skip" "no-agents-root"
    mark_skip
    return 0
  fi
  if ! _wagents_available; then
    log_warn "wagents not available; skipping skills preview."
    record_phase "skills-preview" "skip" "wagents-missing"
    mark_skip
    return 0
  fi
  for id in ${HARNESS_IDS}; do
    extra+=(-a "$id")
  done
  label="$(_wagents_label)"
  log_info "Skills preview (dry-run only): ${label} skills sync --dry-run --format json ${extra[*]}"
  if [ "${APPLY:-0}" -eq 1 ] || [ "${CHECK:-0}" -eq 1 ]; then
    if run_wagents skills sync --dry-run --format json "${extra[@]}"; then
      record_phase "skills-preview" "ok" "dry-run"
      mark_run
      return 0
    fi
    log_warn "Skills preview failed."
    record_phase "skills-preview" "warn" "preview-failed"
    return 0
  fi
  record_phase "skills-preview" "skip" "dry-run-plan"
  mark_skip
}

skills_apply() {
  local -a extra=()
  local id
  if [ "${INSTALL_SKILLS:-0}" -ne 1 ]; then
    record_phase "skills-apply" "skip" "pass --install-skills to run live wagents skills sync --apply"
    mark_skip
    return 0
  fi
  if [ "${APPLY:-0}" -ne 1 ]; then
    log_info "Would apply skills sync for harnesses: ${HARNESS_IDS}"
    record_phase "skills-apply" "skip" "dry-run"
    mark_skip
    return 0
  fi
  if [ -z "${HARNESS_IDS}" ] || [ -z "${AGENTS_ROOT}" ]; then
    record_phase "skills-apply" "skip" "no-harnesses-or-root"
    mark_skip
    return 0
  fi
  if ! _wagents_available; then
    log_warn "wagents not available; skipping live skills apply."
    record_phase "skills-apply" "skip" "wagents-missing"
    mark_skip
    return 0
  fi
  for id in ${HARNESS_IDS}; do
    extra+=(-a "$id")
  done
  if run_wagents skills sync --apply --format json "${extra[@]}"; then
    record_phase "skills-apply" "ok" "applied"
    mark_run
    return 0
  fi
  log_error "Live skills sync failed."
  record_phase "skills-apply" "error" "apply-failed"
  record_blocked "skills-apply"
  return 1
}
