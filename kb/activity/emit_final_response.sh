#!/usr/bin/env bash
# Closure SSOT: read-only verify + per-wave log audit, emit verification-summary.txt verbatim.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "${REPO_ROOT}"

OUT_DIR="${SCRATCH:-/var/folders/z9/yr58561n1rj8_lqtzwkjt24m0000gp/T/grok-goal-cd5f675df757/implementer}"
SUMMARY="${OUT_DIR}/verification-summary.txt"

bash kb/activity/goal-verify.sh >&2
bash kb/activity/per-wave-log-audit.sh >&2

tmp="${SUMMARY}.work.$$"
grep -v '^ac5_per_wave_log' "${SUMMARY}" >"${tmp}" 2>/dev/null || cp "${SUMMARY}" "${tmp}"
{
  cat "${tmp}"
  echo "ac5_per_wave_log_failures: $(awk '/^per_wave_log_failures:/{print $2}' "${OUT_DIR}/per-wave-log-audit.txt")"
  echo "ac5_per_wave_log_result: $(awk '/^per_wave_log_result:/{print $2}' "${OUT_DIR}/per-wave-log-audit.txt")"
} >"${SUMMARY}.new"
mv -f "${SUMMARY}.new" "${SUMMARY}"
rm -f "${tmp}"

exec cat "${SUMMARY}"