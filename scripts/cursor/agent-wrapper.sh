#!/usr/bin/env bash
# Not PATH-installed. Invoke this script by path; it is an optional local helper.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
exec agent --plugin-dir "$ROOT" "$@"
