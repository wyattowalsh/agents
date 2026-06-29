#!/usr/bin/env bash
# Mechanical verifier for goals/kb-research-ingest — mirrors goal/plan.md Verification plan.
# Run from repository root: bash kb/activity/goal-verify.sh
# Writes evidence to SCRATCH/implementer/*.txt (default SCRATCH below).

set -euo pipefail

OUT_DIR="${SCRATCH:-/var/folders/z9/yr58561n1rj8_lqtzwkjt24m0000gp/T/grok-goal-cd5f675df757/implementer}"
REPO_ROOT="$(git rev-parse --show-toplevel)"
TREE="$(git -C "${REPO_ROOT}" rev-parse HEAD)"
BTICK=$'\`'

mkdir -p "${OUT_DIR}"

write_file() {
  local dest="$1"
  shift
  local tmp="${dest}.work.$$"
  "$@" >"${tmp}"
  mv -f "${tmp}" "${dest}"
}

atomic_write() {
  local dest="$1"
  local tmp="${dest}.work.$$"
  cat >"${tmp}"
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
{
  echo "verification_tree: ${TREE}"
  echo "command: uv run python skills/nerdbot/scripts/kb_lint.py --root kb --fail-on warning"
  lint_json="$(uv run python skills/nerdbot/scripts/kb_lint.py --root kb --fail-on warning 2>&1)"
  lint_exit=$?
  echo "${lint_json}"
  echo "exit_code: ${lint_exit}"
  echo "issue_count: $(printf '%s' "${lint_json}" | python3 -c 'import sys,json; print(json.load(sys.stdin)["summary"]["issue_count"])')"
} | atomic_write "${OUT_DIR}/kb-lint.txt"

# --- Step 3: coverage partials (plan §3) ---
{
  echo "verification_tree: ${TREE}"
  echo "command: rg -F '| partial |' kb/indexes/coverage.md"
  if rg -F '| partial |' kb/indexes/coverage.md 2>/dev/null; then
    :
  else
    echo "(no matches)"
  fi
  echo "match_count: $(rg -c -F '| partial |' kb/indexes/coverage.md 2>/dev/null || echo 0)"
} | atomic_write "${OUT_DIR}/coverage-partials.txt"

# --- Step 4: activity waves (plan §4) ---
{
  echo "verification_tree: ${TREE}"
  echo "command_plan_step4: grep -c '^### [' kb/activity/log.md (all dated headers; includes pre-goal history)"
  echo "wave_header_count_all: $(rg -c '^### \[' kb/activity/log.md)"
  echo "macro_wave_count: $(rg -c '### \[2026-06-25\] Wave' kb/activity/log.md)"
  echo "wave_count_2026-06-25: $(rg -c '### \[2026-06-25\] Wave' kb/activity/log.md)"
  echo "plan_step4_gate: macro_wave_count >= 10 (not wave_header_count_all)"
  echo ""
  echo "strict_journal_count: $(rg -c "^- Journal: ${BTICK}~/.grok/research/kb-wave" kb/activity/log.md || echo 0)"
  echo ""
  echo "journal_lines:"
  rg "^- Journal: ${BTICK}~/.grok/research/kb-wave" kb/activity/log.md || true
  echo ""
  echo "log_excerpt_waves_2026-06-25:"
  rg -m5 -A2 '### \[2026-06-25\] Wave' kb/activity/log.md || true
  echo ""
  echo "log_excerpt_closure_2026-06-29:"
  rg -m2 -A6 '### \[2026-06-29\]' kb/activity/goal-closure-notes.md || true
} | atomic_write "${OUT_DIR}/activity-waves.txt"

# --- Step 5: repo-map sourcing (plan §5 — rg cross-check) ---
{
  echo "verification_tree: ${TREE}"
  echo "method: rg primary repo-map Path rows against kb/raw + kb/indexes/source-map.md + kb/wiki"
  missing=0
  checked=0
  while IFS= read -r path; do
    checked=$((checked + 1))
    if rg -Fq "${path}" kb/raw kb/indexes/source-map.md kb/wiki 2>/dev/null; then
      echo "OK: ${path}"
    else
      echo "MISSING: ${path}"
      missing=$((missing + 1))
    fi
  done < <(rg '^\| `' kb/indexes/repo-map.md | awk -F'`' '{print $2}')
  if rg -Fq 'external-primary-source-map' kb/raw kb/wiki 2>/dev/null; then
    echo "OK: External upstream docs (via external-primary-source-map)"
    checked=$((checked + 1))
  else
    echo "MISSING: External upstream docs"
    missing=$((missing + 1))
    checked=$((checked + 1))
  fi
  echo "primary_paths_checked: ${checked}"
  echo "missing_count: ${missing}"
  if [[ ${missing} -eq 0 ]]; then echo "result: PASS"; else echo "result: FAIL"; fi
} | atomic_write "${OUT_DIR}/repo-map-sourced.txt"

# --- Step 6: wave commit scope (plan §6 — last 3 wave commits) ---
{
  echo "verification_tree: ${TREE}"
  echo "audit: last 3 feat(kb): wave commits per verification plan step 6"
  violations=0
  total=0
  while IFS= read -r sha; do
    total=$((total + 1))
    subject="$(git log -1 --pretty=format:%s "${sha}")"
    echo "--- wave sample ${total} ${sha} ---"
    echo "subject: ${subject}"
    git log --name-only -1 --pretty=format:%s "${sha}"
    non_kb="$(git diff-tree --no-commit-id --name-only -r "${sha}" | grep -v '^kb/' || true)"
    if [[ -n "${non_kb}" ]]; then
      violations=$((violations + 1))
      echo "scope_violation: ${non_kb}"
    else
      echo "scope: kb/** only"
    fi
    echo ""
  done < <(git log -3 --reverse --format=%H --grep='feat(kb): wave')
  echo "wave_sample_total: ${total}"
  echo "wave_commit_total_all: $(git log --oneline --grep='feat(kb): wave' | wc -l | tr -d ' ')"
  echo "scope_violations: ${violations}"
} | atomic_write "${OUT_DIR}/commit-evidence.txt"

# --- Step 6b: delivered kb goal commits (wave 01 through HEAD) ---
WAVE_ONE_SHA="$(git log --format=%H --grep='feat(kb): wave 01' -1)"
{
  echo "verification_tree: ${TREE}"
  echo "audit: kb-tagged commits since wave 01 (${WAVE_ONE_SHA:-unknown})"
  violations=0
  total=0
  while IFS= read -r sha; do
    subject="$(git log -1 --pretty=format:%s "${sha}")"
    case "${subject}" in
      feat\(kb\):*|fix\(kb\):*|chore\(kb\):*) ;;
      *) continue ;;
    esac
    total=$((total + 1))
    non_kb="$(git diff-tree --no-commit-id --name-only -r "${sha}" | grep -v '^kb/' || true)"
    if [[ -n "${non_kb}" ]]; then
      violations=$((violations + 1))
      echo "VIOLATION ${sha}: ${subject}"
      echo "${non_kb}"
    fi
  done < <(git log --format=%H "${WAVE_ONE_SHA}"..HEAD 2>/dev/null || true)
  echo "delivered_kb_commits_checked: ${total}"
  echo "delivered_scope_violations: ${violations}"
} | atomic_write "${OUT_DIR}/delivered-commits-audit.txt"

# --- Step 6c: non-kb commits in goal window (must be zero for kb-only goal) ---
{
  echo "verification_tree: ${TREE}"
  echo "audit: any non-kb-tagged commit touching kb/ or any commit in window touching non-kb/"
  window_violations=0
  while IFS= read -r sha; do
    subject="$(git log -1 --pretty=format:%s "${sha}")"
    case "${subject}" in
      feat\(kb\):*|fix\(kb\):*|chore\(kb\):*|test\(kb\):*) continue ;;
    esac
    touches_kb="$(git diff-tree --no-commit-id --name-only -r "${sha}" | grep -c '^kb/' || true)"
    touches_non_kb="$(git diff-tree --no-commit-id --name-only -r "${sha}" | grep -v '^kb/' || true)"
    if [[ -n "${touches_non_kb}" ]]; then
      window_violations=$((window_violations + 1))
      echo "NON_KB_COMMIT ${sha}: ${subject}"
    fi
  done < <(git log --format=%H "${WAVE_ONE_SHA}"..HEAD 2>/dev/null || true)
  echo "goal_window_non_kb_commits: ${window_violations}"
} | atomic_write "${OUT_DIR}/goal-window-scope.txt"

# --- Step 7: final audit (plan §7) ---
{
  echo "verification_tree: ${TREE}"
  echo "=== kb_lint re-run ==="
  uv run python skills/nerdbot/scripts/kb_lint.py --root kb --fail-on warning 2>&1
  echo "lint_exit: $?"
  echo ""
  echo "=== kb_inventory re-run ==="
  uv run python skills/nerdbot/scripts/kb_inventory.py --root kb 2>&1
  echo "inventory_exit: $?"
} | atomic_write "${OUT_DIR}/final-audit.txt"

# --- Step 8: early exit (plan §8) ---
{
  echo "verification_tree: ${TREE}"
  echo "pass 5 early-exit evidence:"
  rg -A4 '### \[2026-06-25\] Wave 29' kb/activity/log.md || true
  echo ""
  rg -A4 '### \[2026-06-25\] Wave 30' kb/activity/log.md || true
  echo ""
  rg 'Waves 29' kb/raw/captures/pass5-final-stop-capture-w30.md || true
} | atomic_write "${OUT_DIR}/early-exit.txt"

# --- Summary (numeric SSOT for capture generator) ---
{
  echo "verification_tree: ${TREE}"
  echo "generated_by: kb/activity/goal-verify.sh"
  echo "timestamp_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "source_map_source_count: $(rg '^source_count:' kb/indexes/source-map.md | head -1)"
  echo "ac1_waves: $(git log --oneline --grep='feat(kb): wave' | wc -l | tr -d ' ')"
  echo "ac1_scope_violations: $(rg '^scope_violations:' "${OUT_DIR}/commit-evidence.txt" || echo 'scope_violations: unknown')"
  echo "ac1_delivered_scope_violations: $(rg '^delivered_scope_violations:' "${OUT_DIR}/delivered-commits-audit.txt" || echo 'delivered_scope_violations: unknown')"
  echo "ac2_partials: $(rg '^match_count:' "${OUT_DIR}/coverage-partials.txt" || true)"
  echo "ac3_repo_map_primary_paths_checked: $(rg '^primary_paths_checked:' "${OUT_DIR}/repo-map-sourced.txt" || true)"
  echo "ac3_repo_map_missing_count: $(rg '^missing_count:' "${OUT_DIR}/repo-map-sourced.txt" || true)"
  echo "ac3_repo_map_result: $(rg '^result:' "${OUT_DIR}/repo-map-sourced.txt" || true)"
  echo "ac4_macro_waves: $(rg '^macro_wave_count:' "${OUT_DIR}/activity-waves.txt" | awk '{print $2}' || true)"
  echo "ac4_waves: $(rg '^wave_count_2026-06-25:' "${OUT_DIR}/activity-waves.txt" || true)"
  echo "ac4_strict_journals: $(rg '^strict_journal_count:' "${OUT_DIR}/activity-waves.txt" || true)"
  echo "ac1_goal_window_non_kb: $(rg '^goal_window_non_kb_commits:' "${OUT_DIR}/goal-window-scope.txt" | awk '{print $2}' || echo unknown)"
  echo "step1_exit: $(rg '^exit_code:' "${OUT_DIR}/kb-inventory.txt" | tail -1)"
  echo "step2_exit: $(rg '^exit_code:' "${OUT_DIR}/kb-lint.txt" | tail -1)"
  echo "step2_issue_count: $(rg '^issue_count:' "${OUT_DIR}/kb-lint.txt" | tail -1)"
  echo "step7_lint_exit: $(rg '^lint_exit:' "${OUT_DIR}/final-audit.txt" | tail -1)"
} | atomic_write "${OUT_DIR}/verification-summary.txt"

# --- Worktree scope (live git status; KB commits kb/** only) ---
{
  echo "verification_tree: ${TREE}"
  echo "kb_goal_scope: closure commits under kb/** only; goals/ is gitignored read-only reference"
  kb_dirty="$(git status --porcelain -- kb/ 2>/dev/null | wc -l | tr -d ' ')"
  unrelated_dirty="$(git status --porcelain 2>/dev/null | { grep -v '^.. kb/' || true; } | wc -l | tr -d ' ')"
  echo "kb_dirty_paths: ${kb_dirty}"
  echo "unrelated_dirty_paths: ${unrelated_dirty}"
  echo "git_status_porcelain:"
  git status --porcelain
} | atomic_write "${OUT_DIR}/worktree-scope.txt"

echo "goal-verify: wrote evidence to ${OUT_DIR} (tree=${TREE})"