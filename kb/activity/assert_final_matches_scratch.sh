#!/usr/bin/env bash
# Fail if candidate FINAL_RESPONSE diverges from scratch verification-summary.txt.

set -euo pipefail

OUT_DIR="${SCRATCH:-/var/folders/z9/yr58561n1rj8_lqtzwkjt24m0000gp/T/grok-goal-cd5f675df757/implementer}"
SCRATCH_SUMMARY="${OUT_DIR}/verification-summary.txt"

if [[ ! -f "${SCRATCH_SUMMARY}" ]]; then
  echo "assert_final_matches_scratch: missing ${SCRATCH_SUMMARY}" >&2
  exit 1
fi

tmpdir="$(mktemp -d)"
trap 'rm -rf "${tmpdir}"' EXIT

if [[ $# -ge 1 && -f "$1" ]]; then
  candidate="${tmpdir}/candidate.txt"
  cp "$1" "${candidate}"
elif [[ $# -ge 1 ]]; then
  echo "assert_final_matches_scratch: not a file: $1" >&2
  exit 1
else
  candidate="${tmpdir}/candidate.txt"
  cat >"${candidate}"
fi

if diff -u "${SCRATCH_SUMMARY}" "${candidate}" >/dev/null 2>&1; then
  echo "assert_final_matches_scratch: PASS"
  exit 0
fi

echo "assert_final_matches_scratch: FAIL" >&2
diff -u "${SCRATCH_SUMMARY}" "${candidate}" >&2 || true
exit 1