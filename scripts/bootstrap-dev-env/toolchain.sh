# Ensure uv, Node/npx, and the wagents CLI.
# shellcheck shell=bash

ensure_uv() {
  if command -v uv >/dev/null 2>&1; then
    log_debug "uv: $(command -v uv)"
    mark_skip
    return 0
  fi
  if [ "${APPLY:-0}" -ne 1 ]; then
    log_info "Would install uv (https://docs.astral.sh/uv/)"
    record_next "Install uv from https://docs.astral.sh/uv/"
    mark_skip
    return 0
  fi
  log_error "uv is required. Install from https://docs.astral.sh/uv/ then re-run."
  record_blocked "uv-missing"
  return 1
}

ensure_node() {
  if command -v node >/dev/null 2>&1 && command -v npx >/dev/null 2>&1; then
    log_debug "node: $(command -v node)"
    mark_skip
    return 0
  fi
  if [ "${APPLY:-0}" -ne 1 ]; then
    log_info "Would require Node.js 22+ with npx"
    record_next "Install Node.js 22+ so npx is available"
    mark_skip
    return 0
  fi
  log_error "Node.js (with npx) is required for skills sync and MCPHub."
  record_blocked "node-missing"
  return 1
}

ensure_wagents() {
  if command -v wagents >/dev/null 2>&1; then
    log_debug "wagents: $(command -v wagents)"
    mark_skip
    return 0
  fi
  if [ -z "${AGENTS_ROOT}" ]; then
    log_warn "Skipping wagents install; agents checkout not resolved."
    mark_skip
    return 0
  fi
  if ! command -v uv >/dev/null 2>&1; then
    log_warn "Skipping wagents install; uv is not available."
    mark_skip
    return 0
  fi
  if [ "${APPLY:-0}" -ne 1 ]; then
    log_info "Would install wagents via uv tool install --from ${AGENTS_ROOT}"
    mark_skip
    return 0
  fi
  if uv tool install --from "${AGENTS_ROOT}" wagents; then
    mark_run
    return 0
  fi
  if uv tool install --from "git+https://github.com/wyattowalsh/agents" wagents; then
    mark_run
    return 0
  fi
  log_warn "Unable to install wagents; continuing with uv run from the checkout."
  mark_skip
  return 0
}

_wagents_available() {
  if command -v wagents >/dev/null 2>&1; then
    return 0
  fi
  if command -v uv >/dev/null 2>&1 && [ -n "${AGENTS_ROOT}" ]; then
    return 0
  fi
  return 1
}

_wagents_label() {
  if command -v wagents >/dev/null 2>&1; then
    printf 'wagents'
    return 0
  fi
  if command -v uv >/dev/null 2>&1 && [ -n "${AGENTS_ROOT}" ]; then
    printf 'uv run wagents'
    return 0
  fi
  return 1
}

run_wagents() {
  if [ -z "${AGENTS_ROOT}" ]; then
    return 1
  fi
  if command -v wagents >/dev/null 2>&1; then
    (cd "${AGENTS_ROOT}" && wagents "$@")
    return $?
  fi
  if command -v uv >/dev/null 2>&1; then
    (cd "${AGENTS_ROOT}" && uv run wagents "$@")
    return $?
  fi
  return 1
}
