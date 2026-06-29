#!/usr/bin/env bash
# Assert each feat(kb): wave commit adds the matching Wave NN header to kb/activity/log.md.

set -euo pipefail

OUT_DIR="${SCRATCH:-/var/folders/z9/yr58561n1rj8_lqtzwkjt24m0000gp/T/grok-goal-cd5f675df757/implementer}"
REPO_ROOT="$(git rev-parse --show-toplevel)"
TREE="$(git -C "${REPO_ROOT}" rev-parse HEAD)"
DEST="${OUT_DIR}/per-wave-log-audit.txt"
TMP="${DEST}.work.$$"
WAVES="${OUT_DIR}/wave-commits.work.$$"

mkdir -p "${OUT_DIR}"
cd "${REPO_ROOT}"

git log --reverse --format='%H %s' --grep='feat(kb): wave' >"${WAVES}"

failures=0
checked=0
{
  echo "verification_tree: ${TREE}"
  echo "audit: each feat(kb): wave NN commit must add ### [2026-06-25] Wave NN to kb/activity/log.md"
  while IFS= read -r line || [[ -n "${line}" ]]; do
    [[ -z "${line}" ]] && continue
    sha="${line%% *}"
    subject="${line#* }"
    if [[ ! "${subject}" =~ ^feat\(kb\):[[:space:]]wave[[:space:]][0-9]+ ]]; then
      continue
    fi
    wave_num="$(printf '%s' "${subject}" | sed -n 's/^feat(kb): wave \([0-9][0-9]*\).*/\1/p')"
    [[ -z "${wave_num}" ]] && continue
    checked=$((checked + 1))
    expected="### [2026-06-25] Wave ${wave_num}"
    diff_text="$(git show "${sha}" -- kb/activity/log.md 2>/dev/null || true)"
    case "${diff_text}" in
      *"${expected}"*)
        echo "OK ${sha}: ${subject} -> ${expected}"
        ;;
      *)
        failures=$((failures + 1))
        echo "FAIL ${sha}: ${subject} missing ${expected} in log.md diff"
        ;;
    esac
  done <"${WAVES}"
  echo "per_wave_log_checked: ${checked}"
  echo "per_wave_log_failures: ${failures}"
  if [[ ${failures} -eq 0 ]]; then
    echo "per_wave_log_result: PASS"
  else
    echo "per_wave_log_result: FAIL"
  fi
} >"${TMP}"
mv -f "${TMP}" "${DEST}"
rm -f "${WAVES}"

if [[ "${failures}" -ne 0 ]]; then
  echo "per-wave-log-audit: FAIL (${failures} failures)" >&2
  exit 1
fi

echo "per-wave-log-audit: PASS — wrote ${DEST}" >&2