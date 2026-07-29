#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"
mcphub_load_env

# Upstream PyPI 1.2.x references Version before the class is defined in
# version_parser.py, which crashes on Python 3.11+. Patch cached installs once.
# Remove this wrapper when upstream ships a fixed wheel (see openspec change
# replace-package-version-check-mcp).
PKG_SPEC="package-version-check-mcp==1.2.20"
STAMP_FILE="${HOME}/.cache/package-version-check-mcp-patched"
STAMP_VERSION="3"

export PATH="/opt/homebrew/bin:/usr/local/bin:${HOME}/.local/bin:${PATH:-}"

launcher_help_ok() {
  mcphub_run_clean GITHUB_PAT -- uvx --from "${PKG_SPEC}" package-version-check-mcp --help >/dev/null 2>&1
}

patch_version_parser_once() {
  if [[ -f "${STAMP_FILE}" ]] && [[ "$(cat "${STAMP_FILE}" 2>/dev/null || true)" == "${STAMP_VERSION}" ]]; then
    if launcher_help_ok; then
      return 0
    fi
    rm -f "${STAMP_FILE}"
  fi

  if launcher_help_ok; then
    mkdir -p "$(dirname "${STAMP_FILE}")"
    printf '%s\n' "${STAMP_VERSION}" >"${STAMP_FILE}"
    return 0
  fi

  local cache_dir parser patched=0
  cache_dir="$(uv cache dir 2>/dev/null || echo "${HOME}/.cache/uv")"
  while IFS= read -r parser; do
    [[ -f "${parser}" ]] || continue
    if head -n 1 "${parser}" | grep -q 'from __future__ import annotations'; then
      patched=1
      continue
    fi
    local tmp
    tmp="$(mktemp)"
    {
      printf '%s\n' 'from __future__ import annotations'
      cat "${parser}"
    } >"${tmp}"
    mv "${tmp}" "${parser}"
    patched=1
  done < <(find "${cache_dir}/archive-v0" -path '*/package_version_check_mcp/utils/version_parser.py' 2>/dev/null | head -20)

  if launcher_help_ok; then
    mkdir -p "$(dirname "${STAMP_FILE}")"
    printf '%s\n' "${STAMP_VERSION}" >"${STAMP_FILE}"
    return 0
  fi

  if [[ "${patched}" -eq 0 ]]; then
    mcphub_run_clean GITHUB_PAT -- uvx --from "${PKG_SPEC}" package-version-check-mcp --help >/dev/null 2>&1 || true
    while IFS= read -r parser; do
      [[ -f "${parser}" ]] || continue
      if head -n 1 "${parser}" | grep -q 'from __future__ import annotations'; then
        patched=1
        continue
      fi
      local tmp
      tmp="$(mktemp)"
      {
        printf '%s\n' 'from __future__ import annotations'
        cat "${parser}"
      } >"${tmp}"
      mv "${tmp}" "${parser}"
      patched=1
    done < <(find "${cache_dir}/archive-v0" -path '*/package_version_check_mcp/utils/version_parser.py' 2>/dev/null | head -20)
  fi

  if ! launcher_help_ok; then
    printf 'package-version-check-mcp: failed to patch or launch upstream package\n' >&2
    return 1
  fi

  mkdir -p "$(dirname "${STAMP_FILE}")"
  printf '%s\n' "${STAMP_VERSION}" >"${STAMP_FILE}"
}

patch_version_parser_once
mcphub_exec_clean GITHUB_PAT -- uvx --from "${PKG_SPEC}" package-version-check-mcp --mode=stdio "$@"
