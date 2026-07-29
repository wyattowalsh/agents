#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

mcphub_setup_runtime_path

tool_dir="${UV_TOOL_DIR:-$(uv tool dir)}"
ddgs_bin="${tool_dir}/ddgs/bin/ddgs"
python_bin="${tool_dir}/ddgs/bin/python"
if [[ ! -x "${ddgs_bin}" || ! -x "${python_bin}" ]]; then
  printf 'ddgs MCP tool is not installed; run: uv tool install --with "mcp<2" "ddgs[mcp]==9.14.4"\n' >&2
  exit 1
fi

versions="$(
  "${python_bin}" -c \
    'import importlib.metadata as m; print(m.version("ddgs"), m.version("mcp"))'
)"
read -r ddgs_version mcp_version <<<"${versions}"
if [[ "${ddgs_version}" != "9.14.4" || "${mcp_version}" != 1.* ]]; then
  printf 'ddgs MCP tool version mismatch: expected ddgs=9.14.4 and mcp=1.x, got ddgs=%s and mcp=%s\n' \
    "${ddgs_version}" "${mcp_version}" >&2
  exit 1
fi

mcphub_exec_clean -- "${ddgs_bin}" mcp "$@"
