# Project repo/home harness surfaces via sync_agent_stack.py.
# shellcheck shell=bash

# Exact names accepted by scripts/sync_agent_stack.py platform_filter_allows().
# Fleet first, then extras. Tests scrape this line and the Python allowlist.
# Never emit remapped tokens: claude, gemini, copilot.
_STACK_PLATFORM_ORDER="repo-core cursor claude-code codex grok opencode vscode crush shared lm-studio"

_stack_platform_known() {
  case " ${_STACK_PLATFORM_ORDER} " in
    *" $1 "*) return 0 ;;
    *) return 1 ;;
  esac
}

_sync_platforms_csv() {
  local id token csv=""
  local selected="repo-core"
  for id in ${HARNESS_IDS}; do
    if ! _stack_platform_known "$id"; then
      continue
    fi
    case " ${selected} " in
      *" ${id} "*) ;;
      *) selected="${selected} ${id}" ;;
    esac
  done
  for token in ${_STACK_PLATFORM_ORDER}; do
    case " ${selected} " in
      *" ${token} "*)
        if [ -n "$csv" ]; then
          csv="${csv},${token}"
        else
          csv="$token"
        fi
        ;;
    esac
  done
  printf '%s' "$csv"
}

sync_stack_repo() {
  local script platforms mode
  if [ -z "${AGENTS_ROOT}" ]; then
    log_warn "Skipping stack sync; agents checkout not resolved."
    record_phase "sync-repo" "skip" "no-agents-root"
    mark_skip
    return 0
  fi
  script="${AGENTS_ROOT}/scripts/sync_agent_stack.py"
  if [ ! -f "$script" ]; then
    log_warn "Missing ${script}"
    record_phase "sync-repo" "skip" "script-missing"
    mark_skip
    return 0
  fi
  if ! command -v uv >/dev/null 2>&1; then
    log_warn "Skipping stack sync; uv is not available."
    record_phase "sync-repo" "skip" "uv-missing"
    mark_skip
    return 0
  fi
  platforms="$(_sync_platforms_csv)"
  if [ "${CHECK:-0}" -eq 1 ] || [ "${APPLY:-0}" -ne 1 ]; then
    mode="--check"
  else
    mode="--apply"
  fi
  if [ "${APPLY:-0}" -ne 1 ] && [ "${CHECK:-0}" -ne 1 ]; then
    log_info "Would run: uv run python ${script} --targets repo --platforms ${platforms} ${mode}"
    record_phase "sync-repo" "skip" "dry-run"
    mark_skip
    return 0
  fi
  if (cd "${AGENTS_ROOT}" && uv run python "$script" --targets repo --platforms "$platforms" "$mode"); then
    record_phase "sync-repo" "ok" "$mode"
    mark_run
    return 0
  fi
  if [ "${CHECK:-0}" -eq 1 ]; then
    log_warn "Stack repo check reported drift."
    record_phase "sync-repo" "warn" "drift"
    return 0
  fi
  log_error "Stack repo sync failed."
  record_phase "sync-repo" "error" "sync-failed"
  record_blocked "sync-repo"
  return 1
}

sync_stack_home() {
  local script platforms mode
  if [ "${HOME_SYNC:-0}" -ne 1 ]; then
    record_phase "sync-home" "skip" "pass --home to project ~/.cursor and other home surfaces"
    mark_skip
    return 0
  fi
  if [ -z "${AGENTS_ROOT}" ]; then
    log_warn "Skipping home sync; agents checkout not resolved."
    record_phase "sync-home" "skip" "no-agents-root"
    mark_skip
    return 0
  fi
  script="${AGENTS_ROOT}/scripts/sync_agent_stack.py"
  if [ ! -f "$script" ] || ! command -v uv >/dev/null 2>&1; then
    record_phase "sync-home" "skip" "missing-uv-or-script"
    mark_skip
    return 0
  fi
  platforms="$(_sync_platforms_csv)"
  if [ "${CHECK:-0}" -eq 1 ] || [ "${APPLY:-0}" -ne 1 ]; then
    mode="--check"
  else
    mode="--apply"
  fi
  if [ "${APPLY:-0}" -ne 1 ] && [ "${CHECK:-0}" -ne 1 ]; then
    log_info "Would run home stack sync --platforms ${platforms} (${mode})"
    record_phase "sync-home" "skip" "dry-run"
    mark_skip
    return 0
  fi
  if (cd "${AGENTS_ROOT}" && uv run python "$script" --targets home --platforms "$platforms" "$mode"); then
    record_phase "sync-home" "ok" "$mode"
    mark_run
    return 0
  fi
  if [ "${CHECK:-0}" -eq 1 ]; then
    log_warn "Stack home check reported drift."
    record_phase "sync-home" "warn" "drift"
    return 0
  fi
  log_error "Stack home sync failed."
  record_phase "sync-home" "error" "sync-failed"
  record_blocked "sync-home"
  return 1
}
