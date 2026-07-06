#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

usage() {
  cat <<'EOF'
Usage: reconcile-runtime.sh [--warm] [--restart]

Copy tracked mcp/mcphub/mcp_settings.json into .mcphub/runtime/mcp_settings.json,
optionally warm package-version-check-mcp, and restart the local LaunchAgent.

  --warm     Run package-version-check-mcp launcher --help before restart
  --restart  kickstart com.wyattowalsh.mcphub (default when any flag is set)
EOF
}

WARM=0
RESTART=0
for arg in "$@"; do
  case "${arg}" in
    --warm) WARM=1 ;;
    --restart) RESTART=1 ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      printf 'unknown argument: %s\n' "${arg}" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ "${WARM}" -eq 0 && "${RESTART}" -eq 0 ]]; then
  WARM=1
  RESTART=1
fi

mcphub_load_env

tracked="${MCPHUB_REPO_ROOT}/mcp/mcphub/mcp_settings.json"
runtime="${MCPHUB_REPO_ROOT}/.mcphub/runtime/mcp_settings.json"
mkdir -p "$(dirname "${runtime}")"
preserve_keys_file="$(mktemp)"
trap 'rm -f "${preserve_keys_file}"' EXIT
if [[ -f "${runtime}" ]]; then
  uv run python - "${runtime}" "${preserve_keys_file}" <<'PY'
import json
import sys
from pathlib import Path

runtime = Path(sys.argv[1])
out = Path(sys.argv[2])
data = json.loads(runtime.read_text(encoding="utf-8"))
keys = data.get("bearerKeys")
if not isinstance(keys, list):
    keys = []
out.write_text(json.dumps(keys), encoding="utf-8")
PY
else
  printf '[]' >"${preserve_keys_file}"
fi
/bin/cp -f "${tracked}" "${runtime}"
uv run python - "${runtime}" "${preserve_keys_file}" <<'PY'
import json
import os
import sys
import uuid
from pathlib import Path

runtime = Path(sys.argv[1])
preserve = Path(sys.argv[2])
data = json.loads(runtime.read_text(encoding="utf-8"))
keys: list[dict] = []
if preserve.exists():
    loaded = json.loads(preserve.read_text(encoding="utf-8"))
    if isinstance(loaded, list):
        keys = loaded
token = (os.environ.get("MCPHUB_BEARER_TOKEN") or "").strip()
if not keys and token and not token.startswith("replace-with-local-"):
    keys = [
        {
            "id": str(uuid.uuid4()),
            "name": "local-control-plane",
            "token": token,
            "enabled": True,
            "kind": "system",
            "accessType": "all",
            "allowedGroups": [],
            "allowedServers": [],
        }
    ]
if keys:
    data["bearerKeys"] = keys
    runtime.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
PY
printf 'synced runtime settings from %s\n' "${tracked}"

launcher="${SCRIPT_DIR}/package-version-check-mcp.sh"
if [[ "${WARM}" -eq 1 && -x "${launcher}" ]]; then
  printf 'warming package-version-check-mcp launcher...\n'
  "${launcher}" --help >/dev/null
  printf 'launcher warm ok\n'
fi

if [[ "${RESTART}" -eq 1 ]]; then
  launchctl kickstart -k "gui/$(id -u)/com.wyattowalsh.mcphub"
  printf 'restarted com.wyattowalsh.mcphub\n'
fi