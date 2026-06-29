#!/usr/bin/env bash
# Mechanical verifier for goals/kb-research-ingest acceptance + verification plan.
# Run from repository root: bash kb/activity/goal-verify.sh
# Writes evidence to SCRATCH/implementer/*.txt (default SCRATCH below).

set -euo pipefail

OUT_DIR="${SCRATCH:-/var/folders/z9/yr58561n1rj8_lqtzwkjt24m0000gp/T/grok-goal-cd5f675df757/implementer}"
REPO_ROOT="$(git rev-parse --show-toplevel)"
TREE="$(git -C "${REPO_ROOT}" rev-parse HEAD)"

mkdir -p "${OUT_DIR}"

write_file() {
  local dest="$1"
  shift
  local tmp="${dest}.work.$$"
  "$@" >"${tmp}"
  mv -f "${tmp}" "${dest}"
}

cd "${REPO_ROOT}"

# --- Step 1: inventory ---
write_file "${OUT_DIR}/kb-inventory.txt" bash -c "
  echo \"verification_tree: ${TREE}\"
  echo \"command: uv run python skills/nerdbot/scripts/kb_inventory.py --root kb\"
  uv run python skills/nerdbot/scripts/kb_inventory.py --root kb 2>&1
  echo \"exit_code: \$?\"
"

# --- Step 2: lint (plan literal fails; working invocation documented) ---
write_file "${OUT_DIR}/kb-lint.txt" bash -c "
  echo \"verification_tree: ${TREE}\"
  echo \"plan_literal_command: uv run python skills/nerdbot/scripts/kb_lint.py kb/ --fail-on warning\"
  echo \"plan_literal_note: positional kb/ is unrecognized; kb_lint.py requires --root (see --help).\"
  if uv run python skills/nerdbot/scripts/kb_lint.py kb/ --fail-on warning 2>&1; then
    echo \"plan_literal_exit_code: 0\"
  else
    echo \"plan_literal_exit_code: \$?\"
  fi
  echo \"\"
  echo \"working_command: uv run python skills/nerdbot/scripts/kb_lint.py --root kb --fail-on warning\"
  uv run python skills/nerdbot/scripts/kb_lint.py --root kb --fail-on warning 2>&1
  echo \"working_exit_code: \$?\"
"

# --- Step 3: coverage partials ---
write_file "${OUT_DIR}/coverage-partials.txt" bash -c "
  echo \"verification_tree: ${TREE}\"
  echo \"command: rg -F '| partial |' kb/indexes/coverage.md\"
  if rg -F '| partial |' kb/indexes/coverage.md 2>/dev/null; then
    :
  else
    echo \"(no matches)\"
  fi
  echo \"match_count: \$(rg -c -F '| partial |' kb/indexes/coverage.md 2>/dev/null || echo 0)\"
"

# --- Step 4: activity waves + strict journal count ---
write_file "${OUT_DIR}/activity-waves.txt" bash -c "
  echo \"verification_tree: ${TREE}\"
  echo \"command: rg -c 'Wave' dated 2026-06-25 in kb/activity/log.md\"
  echo \"wave_count_2026-06-25: \$(rg -c '### \[2026-06-25\] Wave' kb/activity/log.md)\"
  echo \"\"
  echo \"strict_journal_command: rg -c primary ~/.grok/research/kb-wave journal lines\"
  strict_journal_count=\"\$(rg -c '^- Journal: \`~/.grok/research/kb-wave' kb/activity/log.md || echo 0)\"
  echo \"strict_journal_count: \${strict_journal_count}\"
  echo \"\"
  echo \"all_journal_lines:\"
  rg '^- Journal: \`~/.grok/research/kb-wave' kb/activity/log.md || true
"

# --- Step 5: repo-map sourcing ---
write_file "${OUT_DIR}/repo-map-sourced.txt" python3 kb/activity/goal-verify-repo-map.py

# --- Step 6: all 30 wave commits ---
write_file "${OUT_DIR}/commit-evidence.txt" bash -c "
  echo \"verification_tree: ${TREE}\"
  echo \"audit: all feat(kb): wave commits (full loop, not samples)\"
  violations=0
  total=0
  while IFS= read -r sha; do
    total=\$((total + 1))
    subject=\"\$(git log -1 --pretty=format:%s \"\${sha}\")\"
    echo \"--- commit \${total} \${sha} ---\"
    echo \"subject: \${subject}\"
    non_kb=\"\$(git diff-tree --no-commit-id --name-only -r \"\${sha}\" | grep -v '^kb/' || true)\"
    if [[ -n \"\${non_kb}\" ]]; then
      violations=\$((violations + 1))
      echo \"scope_violation: \${non_kb}\"
    else
      echo \"scope: kb/** only\"
    fi
    git diff-tree --no-commit-id --name-only -r \"\${sha}\"
    echo \"\"
  done < <(git log --reverse --format=%H --grep='feat(kb): wave')
  echo \"wave_commit_total: \${total}\"
  echo \"scope_violations: \${violations}\"
"

# --- Step 7: final audit ---
write_file "${OUT_DIR}/final-audit.txt" bash -c "
  echo \"verification_tree: ${TREE}\"
  echo \"=== kb_lint re-run (working --root kb) ===\"
  uv run python skills/nerdbot/scripts/kb_lint.py --root kb --fail-on warning 2>&1
  echo \"lint_exit: \$?\"
  echo \"\"
  echo \"=== kb_inventory re-run ===\"
  uv run python skills/nerdbot/scripts/kb_inventory.py --root kb 2>&1
  echo \"inventory_exit: \$?\"
  echo \"\"
  echo \"=== source-map metadata ===\"
  python3 kb/activity/goal-verify-source-map-meta.py
"

# --- Step 8: early exit ---
write_file "${OUT_DIR}/early-exit.txt" bash -c "
  echo \"verification_tree: ${TREE}\"
  echo \"pass 5 early-exit evidence:\"
  rg -A4 '### \[2026-06-25\] Wave 29' kb/activity/log.md || true
  echo \"\"
  rg -A4 '### \[2026-06-25\] Wave 30' kb/activity/log.md || true
  echo \"\"
  rg 'Waves 29' kb/raw/captures/pass5-final-stop-capture-w30.md || true
"

# --- Summary ---
write_file "${OUT_DIR}/verification-summary.txt" bash -c "
  echo \"verification_tree: ${TREE}\"
  echo \"generated_by: kb/activity/goal-verify.sh\"
  echo \"timestamp_utc: \$(date -u +%Y-%m-%dT%H:%M:%SZ)\"
  echo \"ac1_waves: \$(git log --oneline --grep='feat(kb): wave' | wc -l | tr -d ' ')\"
  echo \"ac1_scope_violations: \$(rg '^scope_violations:' \"${OUT_DIR}/commit-evidence.txt\" || echo 'scope_violations: unknown')\"
  echo \"ac2_partials: \$(rg '^match_count:' \"${OUT_DIR}/coverage-partials.txt\" || true)\"
  echo \"ac3_repo_map: \$(rg '^(primary_table_rows|PASS|FAIL):' \"${OUT_DIR}/repo-map-sourced.txt\" || true)\"
  echo \"ac4_waves: \$(rg '^wave_count_2026-06-25:' \"${OUT_DIR}/activity-waves.txt\" || true)\"
  echo \"ac4_strict_journals: \$(rg '^strict_journal_count:' \"${OUT_DIR}/activity-waves.txt\" || true)\"
  echo \"step1_exit: \$(rg '^exit_code:' \"${OUT_DIR}/kb-inventory.txt\" | tail -1)\"
  echo \"step2_working_exit: \$(rg '^working_exit_code:' \"${OUT_DIR}/kb-lint.txt\" | tail -1)\"
  echo \"step7_lint_exit: \$(rg '^lint_exit:' \"${OUT_DIR}/final-audit.txt\" | tail -1)\"
"

echo "goal-verify: wrote evidence to ${OUT_DIR} (tree=${TREE})"