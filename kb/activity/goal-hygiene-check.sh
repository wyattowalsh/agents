#!/usr/bin/env bash
# Pre-commit hygiene gate for kb-research-ingest closure evidence.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
TREE="$(git -C "${REPO_ROOT}" rev-parse HEAD)"
OUT_DIR="${SCRATCH:-/var/folders/z9/yr58561n1rj8_lqtzwkjt24m0000gp/T/grok-goal-cd5f675df757/implementer}"

cd "${REPO_ROOT}"
fail=0

report() {
  echo "HYGIENE_FAIL: $*"
  fail=1
}

check_pattern() {
  local pattern="$1"
  local target="$2"
  if rg -q "${pattern}" "${target}" 2>/dev/null; then
    report "forbidden pattern '${pattern}' in ${target}"
    rg -n "${pattern}" "${target}" 2>/dev/null | head -3 || true
  fi
}

for target in \
  kb/raw \
  kb/wiki \
  kb/indexes \
  kb/activity/log.md \
  kb/activity/wave-commit-registry.md \
  kb/activity/goal-verification-contract.md \
  kb/raw/captures/goal-closure-audit-capture.md; do
  for pattern in git-log-oracle remediate_ replay_waves 79497d5f 881b5c8a historical_note; do
    check_pattern "${pattern}" "${target}"
  done
  check_pattern 'kb_lint\.py kb/' "${target}"
done

if find kb -name '*.work.*' -print -quit 2>/dev/null | grep -q .; then
  report "stale kb/**/*.work.* temp files present"
  find kb -name '*.work.*' 2>/dev/null | head -5 || true
fi

if [[ -d "${OUT_DIR}" ]]; then
  for file in "${OUT_DIR}"/*.txt; do
    [[ -f "${file}" ]] || continue
    while IFS= read -r sha; do
      if [[ -n "${sha}" && "${sha}" != "${TREE}" ]]; then
        report "scratch ${file} verification_tree ${sha} != HEAD ${TREE}"
      fi
    done < <(rg '^verification_tree:' "${file}" 2>/dev/null | awk '{print $2}' || true)
  done
fi

if [[ "${fail}" -ne 0 ]]; then
  echo "goal-hygiene-check: FAILED (tree=${TREE})"
  exit 1
fi

echo "goal-hygiene-check: PASS (tree=${TREE})"