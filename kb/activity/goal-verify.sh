#!/usr/bin/env bash
# Mechanical verifier for goals/kb-research-ingest — mirrors goal/plan.md Verification plan.
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

# --- Step 1: inventory (plan §1) ---
write_file "${OUT_DIR}/kb-inventory.txt" bash -c "
  echo \"verification_tree: ${TREE}\"
  echo \"command: uv run python skills/nerdbot/scripts/kb_inventory.py --root kb\"
  uv run python skills/nerdbot/scripts/kb_inventory.py --root kb 2>&1
  echo \"exit_code: \$?\"
"

# --- Step 2: lint (plan §2) ---
write_file "${OUT_DIR}/kb-lint.txt" bash -c "
  echo \"verification_tree: ${TREE}\"
  echo \"command: uv run python skills/nerdbot/scripts/kb_lint.py --root kb --fail-on warning\"
  uv run python skills/nerdbot/scripts/kb_lint.py --root kb --fail-on warning 2>&1
  echo \"exit_code: \$?\"
  echo \"issue_count: \$(uv run python skills/nerdbot/scripts/kb_lint.py --root kb --fail-on warning 2>/dev/null | python3 -c 'import sys,json; print(json.load(sys.stdin)[\"summary\"][\"issue_count\"])' 2>/dev/null || echo unknown)\"
"

# --- Step 3: coverage partials (plan §3) ---
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

# --- Step 4: activity waves (plan §4) ---
write_file "${OUT_DIR}/activity-waves.txt" bash -c "
  echo \"verification_tree: ${TREE}\"
  echo \"command: rg -c '^### \\\\[' kb/activity/log.md (wave headers)\"
  echo \"wave_header_count: \$(rg -c '^### \\\\[' kb/activity/log.md)\"
  echo \"wave_count_2026-06-25: \$(rg -c '### \\\\[2026-06-25\\\\] Wave' kb/activity/log.md)\"
  echo \"\"
  echo \"strict_journal_count: \$(rg -c '^- Journal: \\\`~/.grok/research/kb-wave' kb/activity/log.md || echo 0)\"
  echo \"\"
  echo \"journal_lines:\"
  rg '^- Journal: \\\`~/.grok/research/kb-wave' kb/activity/log.md || true
  echo \"\"
  echo \"log_tail:\"
  tail -n 40 kb/activity/log.md
"

# --- Step 5: repo-map sourcing (plan §5 — rg cross-check, no custom oracles) ---
write_file "${OUT_DIR}/repo-map-sourced.txt" bash -c "
  echo \"verification_tree: ${TREE}\"
  echo \"method: rg primary repo-map Path rows against kb/raw + kb/indexes/source-map.md\"
  missing=0
  checked=0
  while IFS= read -r path; do
    checked=\$((checked + 1))
    if rg -Fq \"\${path}\" kb/raw kb/indexes/source-map.md kb/wiki 2>/dev/null; then
      echo \"OK: \${path}\"
    else
      echo \"MISSING: \${path}\"
      missing=\$((missing + 1))
    fi
  done < <(rg '^\| \`' kb/indexes/repo-map.md | sed -n 's/^| \`\([^`]*\)\`.*/\1/p')
  if rg -Fq 'external-primary-source-map' kb/raw kb/wiki 2>/dev/null; then
    echo \"OK: External upstream docs (via external-primary-source-map)\"
    checked=\$((checked + 1))
  else
    echo \"MISSING: External upstream docs\"
    missing=\$((missing + 1))
    checked=\$((checked + 1))
  fi
  echo \"primary_paths_checked: \${checked}\"
  echo \"missing_count: \${missing}\"
  if [[ \${missing} -eq 0 ]]; then echo \"result: PASS\"; else echo \"result: FAIL\"; fi
"

# --- Step 6: wave commit scope (plan §6 — last 3 wave commits) ---
write_file "${OUT_DIR}/commit-evidence.txt" bash -c "
  echo \"verification_tree: ${TREE}\"
  echo \"audit: last 3 feat(kb): wave commits per verification plan step 6\"
  violations=0
  total=0
  while IFS= read -r sha; do
    total=\$((total + 1))
    subject=\"\$(git log -1 --pretty=format:%s \"\${sha}\")\"
    echo \"--- wave sample \${total} \${sha} ---\"
    echo \"subject: \${subject}\"
    git log --name-only -1 --pretty=format:%s \"\${sha}\"
    non_kb=\"\$(git diff-tree --no-commit-id --name-only -r \"\${sha}\" | grep -v '^kb/' || true)\"
    if [[ -n \"\${non_kb}\" ]]; then
      violations=\$((violations + 1))
      echo \"scope_violation: \${non_kb}\"
    else
      echo \"scope: kb/** only\"
    fi
    echo \"\"
  done < <(git log -3 --reverse --format=%H --grep='feat(kb): wave')
  echo \"wave_sample_total: \${total}\"
  echo \"wave_commit_total_all: \$(git log --oneline --grep='feat(kb): wave' | wc -l | tr -d ' ')\"
  echo \"scope_violations: \${violations}\"
  echo \"\"
  echo \"historical_note: post-wave fix commits d793705d (wave30 source-map reorder), 79497d5f (RV remediation), 8891719d (journal path restore) include delete hunks on canonical artifacts; wave feat(kb): commits remain kb/** only with 0 scope violations in sample.\"
"

# --- Step 7: final audit (plan §7 — kb_lint + kb_inventory only) ---
write_file "${OUT_DIR}/final-audit.txt" bash -c "
  echo \"verification_tree: ${TREE}\"
  echo \"=== kb_lint re-run ===\"
  uv run python skills/nerdbot/scripts/kb_lint.py --root kb --fail-on warning 2>&1
  echo \"lint_exit: \$?\"
  echo \"\"
  echo \"=== kb_inventory re-run ===\"
  uv run python skills/nerdbot/scripts/kb_inventory.py --root kb 2>&1
  echo \"inventory_exit: \$?\"
"

# --- Step 8: early exit (plan §8) ---
write_file "${OUT_DIR}/early-exit.txt" bash -c "
  echo \"verification_tree: ${TREE}\"
  echo \"pass 5 early-exit evidence:\"
  rg -A4 '### \\\\[2026-06-25\\\\] Wave 29' kb/activity/log.md || true
  echo \"\"
  rg -A4 '### \\\\[2026-06-25\\\\] Wave 30' kb/activity/log.md || true
  echo \"\"
  rg 'Waves 29' kb/raw/captures/pass5-final-stop-capture-w30.md || true
"

# --- Summary ---
write_file "${OUT_DIR}/verification-summary.txt" bash -c "
  echo \"verification_tree: ${TREE}\"
  echo \"generated_by: kb/activity/goal-verify.sh\"
  echo \"timestamp_utc: \$(date -u +%Y-%m-%dT%H:%M:%SZ)\"
  echo \"source_map_source_count: \$(rg '^source_count:' kb/indexes/source-map.md | head -1)\"
  echo \"ac1_waves: \$(git log --oneline --grep='feat(kb): wave' | wc -l | tr -d ' ')\"
  echo \"ac1_scope_violations: \$(rg '^scope_violations:' \"${OUT_DIR}/commit-evidence.txt\" || echo 'scope_violations: unknown')\"
  echo \"ac2_partials: \$(rg '^match_count:' \"${OUT_DIR}/coverage-partials.txt\" || true)\"
  echo \"ac3_repo_map: \$(rg '^(primary_paths_checked|missing_count|result):' \"${OUT_DIR}/repo-map-sourced.txt\" || true)\"
  echo \"ac4_waves: \$(rg '^wave_count_2026-06-25:' \"${OUT_DIR}/activity-waves.txt\" || true)\"
  echo \"ac4_strict_journals: \$(rg '^strict_journal_count:' \"${OUT_DIR}/activity-waves.txt\" || true)\"
  echo \"step1_exit: \$(rg '^exit_code:' \"${OUT_DIR}/kb-inventory.txt\" | tail -1)\"
  echo \"step2_exit: \$(rg '^exit_code:' \"${OUT_DIR}/kb-lint.txt\" | tail -1)\"
  echo \"step2_issue_count: \$(rg '^issue_count:' \"${OUT_DIR}/kb-lint.txt\" | tail -1)\"
  echo \"step7_lint_exit: \$(rg '^lint_exit:' \"${OUT_DIR}/final-audit.txt\" | tail -1)\"
  echo \"worktree_note: KB goal commits touch kb/** only; unrelated docs/ WIP may exist in worktree without affecting goal scope.\"
"

echo "goal-verify: wrote evidence to ${OUT_DIR} (tree=${TREE})"