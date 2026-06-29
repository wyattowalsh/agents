#!/usr/bin/env bash
# Regenerate goal-closure-audit-capture.md from verification-summary.txt (single HEAD truth).

set -euo pipefail
exec python3 "$(dirname "$0")/goal-capture-template.py" "$@"