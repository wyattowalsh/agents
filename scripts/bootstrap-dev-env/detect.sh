# Profile and harness detection for bootstrap-dev-env.
# shellcheck shell=bash

detect_profile() {
  if [ "${FULL:-0}" -eq 1 ]; then
    PROFILE="maintainer"
  elif [ -n "${CURSOR_AGENT:-}" ] || [ -n "${CURSOR_TRACE_ID:-}" ] || [ "${CURSOR_CLOUD_AGENT:-}" = "1" ]; then
    PROFILE="cloud"
  else
    PROFILE="consumer"
  fi

  if [ "$PROFILE" = "cloud" ] && [ "${WANT_MCPHUB:-0}" -ne 1 ]; then
    SKIP_MCPHUB=1
  fi
}

_harness_has() {
  case " ${HARNESS_IDS} " in
    *" $1 "*) return 0 ;;
    *) return 1 ;;
  esac
}

_add_harness() {
  local id="$1"
  if [ -z "$id" ]; then
    return 0
  fi
  if _harness_has "$id"; then
    return 0
  fi
  if [ -n "$HARNESS_IDS" ]; then
    HARNESS_IDS="${HARNESS_IDS} ${id}"
  else
    HARNESS_IDS="$id"
  fi
}

detect_harnesses() {
  local forced="$1"
  HARNESS_IDS=""

  if [ -n "$forced" ] && [ "$forced" != "auto" ]; then
    HARNESS_IDS="$forced"
    return 0
  fi

  # First-class fleet (same ids as sync_agent_stack --platforms). No remaps.
  if command -v cursor >/dev/null 2>&1 || command -v cursor-agent >/dev/null 2>&1 || command -v agent >/dev/null 2>&1; then
    _add_harness "cursor"
  fi
  if [ -n "${CURSOR_AGENT:-}" ] || [ -n "${CURSOR_TRACE_ID:-}" ]; then
    _add_harness "cursor"
  fi
  if command -v claude >/dev/null 2>&1 || [ -n "${CLAUDECODE:-}" ]; then
    _add_harness "claude-code"
  fi
  if command -v codex >/dev/null 2>&1; then
    _add_harness "codex"
  fi
  if command -v grok >/dev/null 2>&1; then
    _add_harness "grok"
  fi
  if command -v opencode >/dev/null 2>&1; then
    _add_harness "opencode"
  fi

  # Detect-only extras. Skills -a may use these; --platforms only if the name
  # is already in sync_agent_stack.py (crush is; gemini-cli / github-copilot are not).
  if command -v gemini >/dev/null 2>&1; then
    _add_harness "gemini-cli"
  fi
  if command -v copilot >/dev/null 2>&1; then
    _add_harness "github-copilot"
  fi
  if command -v crush >/dev/null 2>&1; then
    _add_harness "crush"
  fi
}
