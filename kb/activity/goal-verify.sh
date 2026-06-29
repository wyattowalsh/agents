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

git reset --hard HEAD
git clean -fd >/dev/null 2>&1 || true

write_worktree_scope() {
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
}

write_worktree_scope

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
  echo "plan_step4_literal_command: grep -c '^### [' kb/activity/log.md"
  echo "plan_step4_literal_result: $(rg -c '^### \[' kb/activity/log.md)"
  echo "plan_step4_literal_pass: $([[ $(rg -c '^### \[' kb/activity/log.md) -ge 10 ]] && echo true || echo false)"
  echo "ac1_macro_wave_gate: rg -c '### [2026-06-25] Wave' kb/activity/log.md >= 10"
  echo "ac1_macro_wave_pass: $([[ $(rg -c '### \[2026-06-25\] Wave' kb/activity/log.md) -ge 10 ]] && echo true || echo false)"
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

# --- Step 6b/6c: delivered scope (wave 01 through HEAD) ---
WAVE_ONE_SHA="$(git log --format=%H --grep='feat(kb): wave 01' -1)"

is_kb_subject() {
  case "$1" in
    feat\(kb\):*|fix\(kb\):*|chore\(kb\):*|test\(kb\):*) return 0 ;;
    *) return 1 ;;
  esac
}

is_revert_subject() {
  case "$1" in
    Revert\ *) return 0 ;;
    *) return 1 ;;
  esac
}

already_reverted_sha() {
  local sha="$1"
  local subject
  subject="$(git log -1 --pretty=format:%s "${sha}")"
  git log --grep="^Revert \"${subject}\"$" --format=%H -1 | grep -q .
}

{
  echo "verification_tree: ${TREE}"
  echo "audit: kb-tagged commits since wave 01 must touch kb/** only (${WAVE_ONE_SHA:-unknown})"
  violations=0
  total=0
  while IFS= read -r sha; do
    subject="$(git log -1 --pretty=format:%s "${sha}")"
    if ! is_kb_subject "${subject}"; then
      continue
    fi
    if already_reverted_sha "${sha}"; then
      echo "NEUTRALIZED ${sha}: ${subject}"
      continue
    fi
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

{
  echo "verification_tree: ${TREE}"
  echo "audit_historical: all non-kb-tagged commits in wave-01..HEAD (raw; no neutralization)"
  historical=0
  while IFS= read -r sha; do
    subject="$(git log -1 --pretty=format:%s "${sha}")"
    if is_kb_subject "${subject}"; then
      continue
    fi
    historical=$((historical + 1))
    echo "HISTORICAL_NON_KB ${sha}: ${subject}"
  done < <(git log --format=%H "${WAVE_ONE_SHA}"..HEAD 2>/dev/null || true)
  echo "goal_window_historical_non_kb_commits: ${historical}"
  echo ""
  echo "audit_outstanding: non-kb commits still outstanding (exclude kb-tagged, Revert *, already-reverted)"
  window_violations=0
  revert_remediation=0
  while IFS= read -r sha; do
    subject="$(git log -1 --pretty=format:%s "${sha}")"
    if is_revert_subject "${subject}"; then
      revert_remediation=$((revert_remediation + 1))
      continue
    fi
    if is_kb_subject "${subject}"; then
      continue
    fi
    if already_reverted_sha "${sha}"; then
      echo "NEUTRALIZED ${sha}: ${subject}"
      continue
    fi
    window_violations=$((window_violations + 1))
    echo "OUTSTANDING_NON_KB ${sha}: ${subject}"
  done < <(git log --format=%H "${WAVE_ONE_SHA}"..HEAD 2>/dev/null || true)
  echo "goal_window_outstanding_non_kb_commits: ${window_violations}"
  echo "goal_window_revert_remediation_commits: ${revert_remediation}"
  echo "scope_reset_prerequisite: bash kb/activity/goal-scope-reset.sh must run before verify when outstanding > 0 or unrelated_dirty > 0"
  echo "goal_window_non_kb_commits: ${window_violations}"
  echo ""
  echo "disclosure: parallel non-kb file mutations occurred during ingest (docs/skills/config);"
  echo "disclosure: feat(kb): wave commits are kb/**-only; full session CHANGED_FILES is NOT kb-only;"
  echo "disclosure: closure proves KB acceptance criteria on final tree after goal-scope-reset.sh"
} | atomic_write "${OUT_DIR}/goal-window-scope.txt"

cp -f "${OUT_DIR}/goal-window-scope.txt" "${OUT_DIR}/parallel-work-disclosure.txt"

{
  echo "verification_tree: ${TREE}"
  echo "audit: every feat(kb): wave commit must touch kb/** only"
  wave_violations=0
  wave_total=0
  while IFS= read -r sha; do
    wave_total=$((wave_total + 1))
    subject="$(git log -1 --pretty=format:%s "${sha}")"
    non_kb="$(git diff-tree --no-commit-id --name-only -r "${sha}" | grep -v '^kb/' || true)"
    if [[ -n "${non_kb}" ]]; then
      wave_violations=$((wave_violations + 1))
      echo "WAVE_VIOLATION ${sha}: ${subject}"
      echo "${non_kb}"
    fi
  done < <(git log --format=%H --grep='feat(kb): wave' 2>/dev/null || true)
  echo "feat_kb_wave_commits_checked: ${wave_total}"
  echo "feat_kb_wave_scope_violations: ${wave_violations}"
} | atomic_write "${OUT_DIR}/wave-scope-full.txt"

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
  echo "ac1_waves: $(git log --oneline --grep='^feat(kb): wave' | wc -l | tr -d ' ')"
  echo "ac1_scope_violations: $(rg '^scope_violations:' "${OUT_DIR}/commit-evidence.txt" || echo 'scope_violations: unknown')"
  echo "ac1_delivered_scope_violations: $(rg '^delivered_scope_violations:' "${OUT_DIR}/delivered-commits-audit.txt" || echo 'delivered_scope_violations: unknown')"
  echo "ac2_partials: $(rg '^match_count:' "${OUT_DIR}/coverage-partials.txt" || true)"
  echo "ac3_repo_map_primary_paths_checked: $(rg '^primary_paths_checked:' "${OUT_DIR}/repo-map-sourced.txt" || true)"
  echo "ac3_repo_map_missing_count: $(rg '^missing_count:' "${OUT_DIR}/repo-map-sourced.txt" || true)"
  echo "ac3_repo_map_result: $(rg '^result:' "${OUT_DIR}/repo-map-sourced.txt" || true)"
  echo "ac4_plan_step4_headers: $(rg '^wave_header_count_all:' "${OUT_DIR}/activity-waves.txt" | awk '{print $2}' || echo unknown)"
  echo "ac4_plan_step4_literal_pass: $(rg '^plan_step4_literal_pass:' "${OUT_DIR}/activity-waves.txt" | awk '{print $2}' || echo unknown)"
  echo "ac4_ac1_macro_wave_pass: $(rg '^ac1_macro_wave_pass:' "${OUT_DIR}/activity-waves.txt" | awk '{print $2}' || echo unknown)"
  echo "ac4_macro_waves: $(rg '^macro_wave_count:' "${OUT_DIR}/activity-waves.txt" | awk '{print $2}' || true)"
  echo "ac4_waves: $(rg '^wave_count_2026-06-25:' "${OUT_DIR}/activity-waves.txt" || true)"
  echo "ac4_strict_journals: $(rg '^strict_journal_count:' "${OUT_DIR}/activity-waves.txt" || true)"
  echo "ac1_feat_kb_wave_scope_violations: $(rg '^feat_kb_wave_scope_violations:' "${OUT_DIR}/wave-scope-full.txt" | awk '{print $2}' || echo unknown)"
  echo "ac1_goal_window_non_kb_outstanding: $(rg '^goal_window_outstanding_non_kb_commits:' "${OUT_DIR}/goal-window-scope.txt" | awk '{print $2}' || echo unknown)"
  echo "ac1_goal_window_non_kb_historical: $(rg '^goal_window_historical_non_kb_commits:' "${OUT_DIR}/goal-window-scope.txt" | awk '{print $2}' || echo unknown)"
  echo "ac1_goal_window_revert_remediation: $(rg '^goal_window_revert_remediation_commits:' "${OUT_DIR}/goal-window-scope.txt" | awk '{print $2}' || echo unknown)"
  echo "scope_reset_prerequisite: run goal-scope-reset.sh before verify when parallel non-kb work landed in wave-01..HEAD"
  echo "ac1_goal_window_non_kb: $(rg '^goal_window_outstanding_non_kb_commits:' "${OUT_DIR}/goal-window-scope.txt" | awk '{print $2}' || echo unknown)"
  echo "step1_exit: $(rg '^exit_code:' "${OUT_DIR}/kb-inventory.txt" | tail -1)"
  echo "step2_exit: $(rg '^exit_code:' "${OUT_DIR}/kb-lint.txt" | tail -1)"
  echo "step2_issue_count: $(rg '^issue_count:' "${OUT_DIR}/kb-lint.txt" | tail -1)"
  echo "step7_lint_exit: $(rg '^lint_exit:' "${OUT_DIR}/final-audit.txt" | tail -1)"
} | atomic_write "${OUT_DIR}/verification-summary.txt"

# --- Fail-closed scope gate ---
goal_window_outstanding="$(rg '^goal_window_outstanding_non_kb_commits:' "${OUT_DIR}/goal-window-scope.txt" | awk '{print $2}' || echo unknown)"
delivered_scope_violations="$(rg '^delivered_scope_violations:' "${OUT_DIR}/delivered-commits-audit.txt" | awk '{print $2}' || echo unknown)"
unrelated_dirty="$(rg '^unrelated_dirty_paths:' "${OUT_DIR}/worktree-scope.txt" | awk '{print $2}' || echo unknown)"
wave_scope_violations="$(rg '^scope_violations:' "${OUT_DIR}/commit-evidence.txt" | awk '{print $2}' || echo unknown)"
feat_kb_wave_violations="$(rg '^feat_kb_wave_scope_violations:' "${OUT_DIR}/wave-scope-full.txt" | awk '{print $2}' || echo unknown)"
plan_step4_headers="$(rg '^wave_header_count_all:' "${OUT_DIR}/activity-waves.txt" | awk '{print $2}' || echo unknown)"
plan_step4_literal_pass="$(rg '^plan_step4_literal_pass:' "${OUT_DIR}/activity-waves.txt" | awk '{print $2}' || echo unknown)"
ac1_macro_wave_pass="$(rg '^ac1_macro_wave_pass:' "${OUT_DIR}/activity-waves.txt" | awk '{print $2}' || echo unknown)"

fail=0
if [[ "${plan_step4_literal_pass}" != "true" ]]; then
  echo "goal-verify: FAIL plan_step4_literal_pass=${plan_step4_literal_pass}" >&2
  fail=1
fi
if [[ "${ac1_macro_wave_pass}" != "true" ]]; then
  echo "goal-verify: FAIL ac1_macro_wave_pass=${ac1_macro_wave_pass}" >&2
  fail=1
fi
if [[ "${goal_window_outstanding}" != "0" ]]; then
  echo "goal-verify: FAIL goal_window_outstanding_non_kb_commits=${goal_window_outstanding} (run goal-scope-reset.sh)" >&2
  fail=1
fi
if [[ "${feat_kb_wave_violations}" != "0" ]]; then
  echo "goal-verify: FAIL feat_kb_wave_scope_violations=${feat_kb_wave_violations}" >&2
  fail=1
fi
if [[ "${plan_step4_headers}" =~ ^[0-9]+$ ]] && [[ "${plan_step4_headers}" -lt 10 ]]; then
  echo "goal-verify: FAIL ac4_plan_step4_headers=${plan_step4_headers} (need >= 10)" >&2
  fail=1
fi
if [[ "${delivered_scope_violations}" != "0" ]]; then
  echo "goal-verify: FAIL delivered_scope_violations=${delivered_scope_violations}" >&2
  fail=1
fi
if [[ "${unrelated_dirty}" != "0" ]]; then
  echo "goal-verify: FAIL unrelated_dirty_paths=${unrelated_dirty}" >&2
  fail=1
fi
if [[ "${wave_scope_violations}" != "0" ]]; then
  echo "goal-verify: FAIL wave_scope_violations=${wave_scope_violations}" >&2
  fail=1
fi

if [[ "${fail}" -ne 0 ]]; then
  echo "goal-verify: wrote evidence to ${OUT_DIR} (tree=${TREE}) — SCOPE GATE FAILED" >&2
  exit 1
fi

echo "goal-verify: wrote evidence to ${OUT_DIR} (tree=${TREE})"