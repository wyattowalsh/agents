# Locate or shallow-clone the agents checkout.
# shellcheck shell=bash

# Keep identical to dotfiles/rig/bootstrap/dev-env.sh _is_agents_repo.
_is_agents_repo() {
  local path="$1"
  if [ ! -d "${path}/skills" ]; then
    return 1
  fi
  if [ -f "${path}/agent-bundle.json" ] || [ -f "${path}/AGENTS.md" ]; then
    return 0
  fi
  if [ -d "${path}/agents" ] && [ -f "${path}/pyproject.toml" ]; then
    return 0
  fi
  return 1
}

locate_agents_root() {
  local candidate script_root parent

  AGENTS_ROOT=""

  if [ -n "${WAGENTS_REPO_ROOT:-}" ]; then
    candidate="${WAGENTS_REPO_ROOT}"
    if _is_agents_repo "$candidate"; then
      AGENTS_ROOT="$(cd "$candidate" && pwd)"
      return 0
    fi
    log_warn "WAGENTS_REPO_ROOT is set but is not an agents checkout: ${candidate}"
  fi

  for candidate in "${HOME}/dev/projects/agents" "${HOME}/dev/tools/agents"; do
    if _is_agents_repo "$candidate"; then
      AGENTS_ROOT="$(cd "$candidate" && pwd)"
      return 0
    fi
  done

  script_root="$(cd "${BOOT_SCRIPT_DIR}/.." && pwd)"
  if _is_agents_repo "$script_root"; then
    AGENTS_ROOT="$script_root"
    return 0
  fi

  parent="$(cd "${script_root}/.." && pwd)"
  if _is_agents_repo "${parent}/agents"; then
    AGENTS_ROOT="$(cd "${parent}/agents" && pwd)"
    return 0
  fi

  return 1
}

clone_agents_if_needed() {
  local dest="${CLONE_DIR}"
  if [ -n "${AGENTS_ROOT}" ]; then
    return 0
  fi
  if [ -e "$dest" ] && ! _is_agents_repo "$dest"; then
    log_error "Refusing to clone over a non-repo path: ${dest}"
    record_blocked "clone-destination-exists"
    return 1
  fi
  if [ "${APPLY:-0}" -ne 1 ]; then
    log_info "Would clone https://github.com/wyattowalsh/agents.git into ${dest}"
    mark_skip
    record_next "git clone --depth 1 https://github.com/wyattowalsh/agents.git ${dest}"
    return 0
  fi
  mkdir -p "$(dirname "$dest")"
  if git clone --depth 1 https://github.com/wyattowalsh/agents.git "$dest"; then
    AGENTS_ROOT="$(cd "$dest" && pwd)"
    mark_run
    return 0
  fi
  log_error "Failed to clone agents repository into ${dest}"
  record_blocked "clone-failed"
  return 1
}
