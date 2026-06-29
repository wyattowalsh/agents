#!/usr/bin/env bash
# Grok delegate preflight: bundled portable doctor (no wagents dependency).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "${SCRIPT_DIR}/doctor.py" --format json "$@"