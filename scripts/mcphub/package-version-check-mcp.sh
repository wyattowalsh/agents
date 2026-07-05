#!/usr/bin/env bash
set -euo pipefail

# Upstream PyPI 1.2.x references Version before the class is defined in
# version_parser.py, which crashes on Python 3.11+. Patch cached installs once.
STAMP_FILE="${HOME}/.cache/package-version-check-mcp-patched"
STAMP_VERSION="1"

patch_version_parser_once() {
  if [[ -f "${STAMP_FILE}" ]] && [[ "$(cat "${STAMP_FILE}" 2>/dev/null || true)" == "${STAMP_VERSION}" ]]; then
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
  done < <(find "${cache_dir}" -path '*/package_version_check_mcp/utils/version_parser.py' 2>/dev/null | head -20)
  if [[ "${patched}" -eq 1 ]]; then
    mkdir -p "$(dirname "${STAMP_FILE}")"
    printf '%s\n' "${STAMP_VERSION}" >"${STAMP_FILE}"
  fi
}

export PATH="/opt/homebrew/bin:/usr/local/bin:${HOME}/.local/bin:${PATH:-}"
patch_version_parser_once
exec uvx package-version-check-mcp --mode=stdio "$@"