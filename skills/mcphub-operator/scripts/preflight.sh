#!/usr/bin/env bash
# MCPHub operator preflight: bundled portable doctor.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "${SCRIPT_DIR}/doctor.py" --format json "$@"