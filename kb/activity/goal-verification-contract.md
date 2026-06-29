---
title: Goal Verification Contract
tags:
  - kb
  - activity
  - meta
aliases:
  - KB research ingest verification contract
kind: index
status: active
updated: 2026-06-29
source_count: 1
---

# KB Research Ingest — Verification Contract

Committed mirror of the goal verification plan (session `goal/plan.md`). The gitignored `goals/kb-research-ingest/` package is read-only reference per goal non-goals.

## Closure pipeline (order matters)

| Step | Command |
|------|---------|
| Scope reset (conditional) | `bash kb/activity/goal-scope-reset.sh` — only when `goal_window_outstanding_non_kb_commits` > 0 |
| Emit FINAL_RESPONSE | `bash kb/activity/emit_final_response.sh` — read-only verify + per-wave log audit + verbatim summary |
| Hygiene | `bash kb/activity/goal-hygiene-check.sh` |
| Contract tests | `uv run pytest kb/activity/test_goal_verify.py -q` |
| Assert prose SSOT | `bash kb/activity/assert_final_matches_scratch.sh candidate.txt` |
| Capture (optional) | `SCRATCH=… bash kb/activity/goal-capture-template.sh` |

`goal-verify.sh` is read-only on committed `HEAD` (no `git reset --hard`). `unrelated_dirty_paths` is informational only.

## Plan step → scratch artifact map

| Plan § | Scratch artifact | Summary field(s) |
|--------|------------------|------------------|
| 1 | `kb-inventory.txt` | `step1_exit` |
| 2 | `kb-lint.txt` | `step2_issue_count`, `step2_exit` |
| 3 | `coverage-partials.txt` | `ac2_partials` |
| 4 | `activity-waves.txt` | `ac4_plan_step4_headers`, `ac4_plan_step4_literal_pass`, `ac4_macro_waves`, `ac4_ac1_macro_wave_pass` |
| 5 | `repo-map-sourced.txt` | `ac3_repo_map_result` |
| 6 | `commit-evidence.txt` | `ac1_scope_violations` (last 3 `feat(kb): wave [0-9]+` only) |
| 6b | `wave-scope-full.txt` | `ac1_feat_kb_wave_scope_violations`, `ac1_waves` |
| 6c | `goal-window-scope.txt` | `ac1_goal_window_non_kb_outstanding`, `ac1_goal_window_non_kb_historical` |
| 6d | `per-wave-log-audit.txt` | `per_wave_log_result` (via `per-wave-log-audit.sh`) |
| 7 | `final-audit.txt` | `step7_lint_exit` |
| 8 | `early-exit.txt` | (pass-5 stop evidence when applicable) |
| — | `verification-summary.txt` | **FINAL_RESPONSE SSOT** |
| — | `parallel-work-disclosure.txt` | copy of goal-window tail + `session_changed_files_non_kb: true` |

## KB substance commands (plan steps 1–8)

| Step | Command |
|------|---------|
| Inventory | `uv run python skills/nerdbot/scripts/kb_inventory.py --root kb` |
| Lint | `uv run python skills/nerdbot/scripts/kb_lint.py --root kb --fail-on warning` |
| Partials | `rg -F '| partial |' kb/indexes/coverage.md` → 0 matches |
| Waves (plan §4 literal) | `grep -c '^### [' kb/activity/log.md` ≥ 10 (`plan_step4_literal_pass`; includes pre-goal headers) |
| Macro-waves (AC1) | `rg -c '### \[2026-06-25\] Wave' kb/activity/log.md` ≥ 10 (`ac1_macro_wave_pass`; 30 delivered) |
| Repo-map | cross-check primary table paths in `kb/raw`, `kb/wiki`, `kb/indexes/source-map.md` |
| Wave scope | every `feat(kb): wave [0-9]+` commit touches `kb/**` only (`wave-scope-full.txt`) |
| Per-wave log | each wave commit adds matching `### [2026-06-25] Wave NN` in `log.md` diff (`per-wave-log-audit.sh`) |

## Source count SSOT

`kb/indexes/source-map.md` frontmatter `source_count: 153` is the only authoritative count. Do not cite 122 or inventory-only totals in closure prose.

## Scope honesty

- **Historical pollution:** `goal_window_historical_non_kb_commits` counts all non-kb-tagged commits in wave-01..HEAD (parallel docs/grok work during ingest). Expected > 0 after remediation reverts land.
- **Outstanding pollution:** `goal_window_outstanding_non_kb_commits` must be 0 at verify time (after `goal-scope-reset.sh`).
- **Wave delivery:** all 30 `feat(kb): wave` commits are kb/**-only; this is verified directly without reset.
- Closure does **not** claim the entire goal session never touched non-kb paths — it claims KB acceptance criteria hold on the final tree after explicit scope neutralization.
- `parallel-work-disclosure.txt` (copy of `goal-window-scope.txt` tail) documents that parallel docs/skills/config mutations occurred; only `feat(kb): wave` delivery commits are kb/**-only.
- Numeric prose must come from scratch `verification-summary.txt` verbatim — never hand-type counts or commit SHAs.

## Acceptance gates

- `issue_count: 0` from kb_lint JSON summary
- `source_count: 153` in `kb/indexes/source-map.md`
- `ac1_feat_kb_wave_scope_violations: 0`
- `ac1_goal_window_non_kb_outstanding: 0` (post-reset when needed)
- `session_changed_files_non_kb: true`
- `per_wave_log_result: PASS`
- FINAL_RESPONSE stdout equals scratch `verification-summary.txt` byte-for-byte
- Scratch `verification_tree` must equal `git rev-parse HEAD` on every `*.txt` artifact