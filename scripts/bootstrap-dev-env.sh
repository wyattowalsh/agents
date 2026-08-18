#!/usr/bin/env bash
# Portable consumer/maintainer agent-dev-env bootstrap.
# Default: dry-run. Logs on stderr. --format json writes the report on stdout.
set -euo pipefail

BOOT_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOOT_LIB="${BOOT_SCRIPT_DIR}/bootstrap-dev-env"

# shellcheck source=bootstrap-dev-env/common.sh
source "${BOOT_LIB}/common.sh"
# shellcheck source=bootstrap-dev-env/detect.sh
source "${BOOT_LIB}/detect.sh"
# shellcheck source=bootstrap-dev-env/locate.sh
source "${BOOT_LIB}/locate.sh"
# shellcheck source=bootstrap-dev-env/toolchain.sh
source "${BOOT_LIB}/toolchain.sh"
# shellcheck source=bootstrap-dev-env/sync.sh
source "${BOOT_LIB}/sync.sh"
# shellcheck source=bootstrap-dev-env/skills.sh
source "${BOOT_LIB}/skills.sh"
# shellcheck source=bootstrap-dev-env/hooks.sh
source "${BOOT_LIB}/hooks.sh"
# shellcheck source=bootstrap-dev-env/mcphub.sh
source "${BOOT_LIB}/mcphub.sh"
# shellcheck source=bootstrap-dev-env/doctors.sh
source "${BOOT_LIB}/doctors.sh"
# shellcheck source=bootstrap-dev-env/report.sh
source "${BOOT_LIB}/report.sh"

DRY_RUN=1
APPLY=0
CHECK=0
VERBOSE=0
FORMAT="text"
PROFILE="consumer"
AGENTS_ROOT=""
HARNESS_IDS=""
HARNESS_FORCED=""
HOME_SYNC=0
INSTALL_SKILLS=0
SKIP_MCPHUB=0
WANT_MCPHUB=0
REQUIRE=0
FULL=0
CLONE_DIR="${HOME}/dev/projects/agents"

usage() {
  cat <<'USAGE'
Usage: scripts/bootstrap-dev-env.sh [--dry-run | --apply | --check] [options]

Preview by default. Mutate only with --apply.

First-class fleet (plus repo-core when --platforms is passed):
  Cursor, Claude Code, Codex, Grok Build, OpenCode

Journeys
  Laptop                       ./scripts/bootstrap-dev-env.sh
                               ./scripts/bootstrap-dev-env.sh --apply
  JSON for coding agents       ./scripts/bootstrap-dev-env.sh --format json
  Debian / WSL / Codespace     called from dotfiles ./setup.sh
  Cursor Cloud Agent           --skip-mcphub (auto when CURSOR_AGENT is set)

Flags
  --dry-run          Print the plan (default). Platforms = fleet ∩ detected +
                     repo-core. Does not start MCPHub.
  --apply            Project those platforms. Still does not start MCPHub.
  --check            Verify only; fail on drift
  --verbose          Debug logs
  --format text|json Default text; JSON on stdout, logs on stderr
  --harness ID       Repeatable. Restrict to fleet ids: cursor, claude-code,
                     codex, grok, opencode (or other allowlisted stack names).
  --home             Also project home harness files (~/.cursor, …)
  --install-skills   Live wagents skills sync --apply (off by default)
  --full             Maintainer path (uv sync + validate)
  --skip-mcphub      No hub start; skip settings check
  --mcphub           Start local MCPHub via start-local-only.sh (never tunnel)
  --require          Treat warnings as errors
  --clone-dir PATH   Clone destination if no checkout exists
  -h, --help         This help

Never: print secrets, write Cursor cli-config/state.vscdb, marketplace-add
plugins, npx skills add --skill '*', or start the Cloudflare tunnel.

Examples
  ./scripts/bootstrap-dev-env.sh
  ./scripts/bootstrap-dev-env.sh --apply
  ./scripts/bootstrap-dev-env.sh --format json --harness cursor --harness claude-code
USAGE
}

_valid_harness() {
  case "$1" in
    auto|cursor|claude-code|codex|grok|opencode|crush|vscode|shared|lm-studio|gemini-cli|github-copilot) return 0 ;;
    *) return 1 ;;
  esac
}

parse_args() {
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --dry-run) DRY_RUN=1; APPLY=0; CHECK=0 ;;
      --apply) APPLY=1; DRY_RUN=0; CHECK=0 ;;
      --check) CHECK=1; APPLY=0; DRY_RUN=0 ;;
      --verbose) VERBOSE=1 ;;
      --format)
        shift
        FORMAT="${1:-}"
        if [ "$FORMAT" != "text" ] && [ "$FORMAT" != "json" ]; then
          printf 'Unknown --format: %s\n' "$FORMAT" >&2
          exit 2
        fi
        ;;
      --harness)
        shift
        if [ -z "${1:-}" ] || ! _valid_harness "$1"; then
          printf 'Unknown --harness: %s\n' "${1:-}" >&2
          exit 2
        fi
        if [ "$1" != "auto" ]; then
          if [ -n "$HARNESS_FORCED" ]; then
            HARNESS_FORCED="${HARNESS_FORCED} $1"
          else
            HARNESS_FORCED="$1"
          fi
        fi
        ;;
      --home) HOME_SYNC=1 ;;
      --install-skills) INSTALL_SKILLS=1 ;;
      --full) FULL=1 ;;
      --skip-mcphub) SKIP_MCPHUB=1; WANT_MCPHUB=0 ;;
      --mcphub) WANT_MCPHUB=1; SKIP_MCPHUB=0 ;;
      --require) REQUIRE=1 ;;
      --clone-dir)
        shift
        CLONE_DIR="${1:-}"
        if [ -z "$CLONE_DIR" ]; then
          printf '--clone-dir requires a path\n' >&2
          exit 2
        fi
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        printf 'Unknown option: %s\n' "$1" >&2
        usage >&2
        exit 2
        ;;
    esac
    shift
  done
}

refuse_windows() {
  case "$(uname -s)" in
    MINGW*|MSYS*|CYGWIN*|Windows_NT)
      printf 'Windows native is not supported. Use WSL2 (Debian/Ubuntu).\n' >&2
      exit 2
      ;;
  esac
}

run_full_extras() {
  if [ "${FULL:-0}" -ne 1 ]; then
    return 0
  fi
  if [ -z "${AGENTS_ROOT}" ]; then
    record_phase "full" "skip" "no-agents-root"
    return 0
  fi
  if [ "${APPLY:-0}" -ne 1 ]; then
    log_info "Would run: uv sync && uv run wagents validate"
    record_phase "full" "skip" "dry-run"
    mark_skip
    return 0
  fi
  if command -v uv >/dev/null 2>&1; then
    (cd "${AGENTS_ROOT}" && uv sync && uv run wagents validate) || {
      log_warn "Maintainer uv sync / validate reported issues."
      record_phase "full" "warn" "validate"
      return 0
    }
    record_phase "full" "ok" "validated"
    mark_run
  else
    record_phase "full" "skip" "uv-missing"
    mark_skip
  fi
}

main() {
  parse_args "$@"
  refuse_windows
  trap release_lock EXIT
  acquire_lock

  log_info "[1/9] Detect profile and harnesses"
  detect_profile
  detect_harnesses "${HARNESS_FORCED:-auto}"
  record_phase "preflight" "ok" "profile=${PROFILE}"

  log_info "[2/9] Locate agents checkout"
  if locate_agents_root; then
    record_phase "locate" "ok" "${AGENTS_ROOT}"
  else
    record_phase "locate" "skip" "not-found"
    clone_agents_if_needed || true
    if [ -n "${AGENTS_ROOT}" ]; then
      record_phase "locate" "ok" "${AGENTS_ROOT}"
    fi
  fi

  log_info "[3/9] Toolchain (uv, node, wagents)"
  ensure_uv || true
  ensure_node || true
  ensure_wagents || true
  record_phase "toolchain" "ok" "checked"

  log_info "[4/9] Project repo harness surfaces"
  sync_stack_repo || true

  log_info "[5/9] Optional home projection"
  sync_stack_home || true

  log_info "[6/9] Skills preview"
  skills_preview || true
  skills_apply || true

  log_info "[7/9] Hooks"
  hooks_validate || true
  run_full_extras || true

  log_info "[8/9] MCPHub (local only, no tunnel)"
  mcphub_check_settings || true
  mcphub_start_local_if_requested || true

  log_info "[9/9] Optional doctors"
  run_optional_doctors || true

  emit_report
}

main "$@"
