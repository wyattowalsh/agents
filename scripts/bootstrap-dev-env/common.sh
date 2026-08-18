# Shared logging, counters, lock, and JSON helpers for bootstrap-dev-env.
# shellcheck shell=bash

COUNTER_RUN=0
COUNTER_SKIP=0
COUNTER_WARN=0
COUNTER_ERROR=0
PHASES_TEXT=""
BLOCKED_TEXT=""
NEXT_TEXT=""
BOOT_LOCK_DIR=""

_boot_color_enabled() {
  if [ ! -t 2 ] || [ -n "${NO_COLOR:-}" ]; then
    return 1
  fi
  return 0
}

log_info() {
  if _boot_color_enabled; then
    printf '\033[1;34m[info]\033[0m %s\n' "$*" >&2
  else
    printf '[info] %s\n' "$*" >&2
  fi
}

log_warn() {
  COUNTER_WARN=$((COUNTER_WARN + 1))
  if _boot_color_enabled; then
    printf '\033[1;33m[warn]\033[0m %s\n' "$*" >&2
  else
    printf '[warn] %s\n' "$*" >&2
  fi
}

log_error() {
  COUNTER_ERROR=$((COUNTER_ERROR + 1))
  if _boot_color_enabled; then
    printf '\033[1;31m[error]\033[0m %s\n' "$*" >&2
  else
    printf '[error] %s\n' "$*" >&2
  fi
}

log_debug() {
  if [ "${VERBOSE:-0}" -eq 1 ]; then
    printf '[debug] %s\n' "$*" >&2
  fi
}

mark_run() {
  COUNTER_RUN=$((COUNTER_RUN + 1))
}

mark_skip() {
  COUNTER_SKIP=$((COUNTER_SKIP + 1))
}

mark_warn() {
  log_warn "$@"
}

mark_error() {
  log_error "$@"
}

record_phase() {
  local id="$1"
  local status="$2"
  local detail="${3:-}"
  detail="$(printf '%s' "$detail" | tr '|\n' '  ')"
  if [ -n "$PHASES_TEXT" ]; then
    PHASES_TEXT="${PHASES_TEXT}
${id}|${status}|${detail}"
  else
    PHASES_TEXT="${id}|${status}|${detail}"
  fi
}

record_blocked() {
  local item="$1"
  if [ -n "$BLOCKED_TEXT" ]; then
    BLOCKED_TEXT="${BLOCKED_TEXT}
${item}"
  else
    BLOCKED_TEXT="$item"
  fi
}

record_next() {
  local item="$1"
  if [ -n "$NEXT_TEXT" ]; then
    NEXT_TEXT="${NEXT_TEXT}
${item}"
  else
    NEXT_TEXT="$item"
  fi
}

run_or_print() {
  local description="$1"
  shift
  if [ "${APPLY:-0}" -ne 1 ]; then
    printf '[dry-run] %s:' "$description" >&2
    printf ' %q' "$@" >&2
    printf '\n' >&2
    mark_skip
    return 0
  fi
  log_info "$description"
  "$@"
  mark_run
}

json_escape() {
  local s="$1"
  s="${s//\\/\\\\}"
  s="${s//\"/\\\"}"
  s="${s//$'\n'/\\n}"
  s="${s//$'\r'/\\r}"
  s="${s//$'\t'/\\t}"
  printf '%s' "$s"
}

acquire_lock() {
  local base
  if [ "${APPLY:-0}" -ne 1 ]; then
    return 0
  fi
  base="${XDG_RUNTIME_DIR:-${HOME}/.cache}/wagents"
  mkdir -p "$base"
  BOOT_LOCK_DIR="${base}/bootstrap-dev-env.lock"
  if mkdir "$BOOT_LOCK_DIR" 2>/dev/null; then
    return 0
  fi
  log_error "Another bootstrap-dev-env run holds ${BOOT_LOCK_DIR}"
  return 1
}

release_lock() {
  if [ -n "${BOOT_LOCK_DIR}" ] && [ -d "${BOOT_LOCK_DIR}" ]; then
    rmdir "${BOOT_LOCK_DIR}" 2>/dev/null || true
  fi
}
