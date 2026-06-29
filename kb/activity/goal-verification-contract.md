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
| Scope reset | `bash kb/activity/goal-scope-reset.sh` — neutralize outstanding non-kb commits + dirty worktree |
| Verify | `bash kb/activity/goal-verify.sh` |
| Hygiene | `bash kb/activity/goal-hygiene-check.sh` |
| Contract tests | `uv run pytest kb/activity/test_goal_verify.py -q` |
| Capture | `SCRATCH=… bash kb/activity/goal-capture-template.sh` |

## KB substance commands (plan steps 1–8)

| Step | Command |
|------|---------|
| Inventory | `uv run python skills/nerdbot/scripts/kb_inventory.py --root kb` |
| Lint | `uv run python skills/nerdbot/scripts/kb_lint.py --root kb --fail-on warning` |
| Partials | `rg -F '| partial |' kb/indexes/coverage.md` → 0 matches |
| Waves (plan §4) | `grep -c '^### [' kb/activity/log.md` ≥ 10 |
| Macro-waves (AC1) | `rg -c '### \[2026-06-25\] Wave' kb/activity/log.md` ≥ 10 (30 delivered) |
| Repo-map | cross-check primary table paths in `kb/raw`, `kb/wiki`, `kb/indexes/source-map.md` |
| Wave scope | every `feat(kb): wave` commit touches `kb/**` only (`wave-scope-full.txt`) |
| KB-tagged delivery | active `feat|fix|chore|test(kb):` since wave 01 touch `kb/**` only |

## Source count SSOT

`kb/indexes/source-map.md` frontmatter `source_count: 153` is the only authoritative count. Do not cite 122 or inventory-only totals in closure prose.

## Scope honesty

- **Historical pollution:** `goal_window_historical_non_kb_commits` counts all non-kb-tagged commits in wave-01..HEAD (parallel docs/grok work during ingest). Expected > 0 after remediation reverts land.
- **Outstanding pollution:** `goal_window_outstanding_non_kb_commits` must be 0 at verify time (after `goal-scope-reset.sh`).
- **Wave delivery:** all 30 `feat(kb): wave` commits are kb/**-only; this is verified directly without reset.
- Closure does **not** claim the entire goal session never touched non-kb paths — it claims KB acceptance criteria hold on the final tree after explicit scope neutralization.

## Acceptance gates

- `issue_count: 0` from kb_lint JSON summary
- `source_count: 153` in `kb/indexes/source-map.md`
- `ac1_feat_kb_wave_scope_violations: 0`
- `ac1_goal_window_non_kb_outstanding: 0` (post-reset)
- Scratch `verification_tree` must equal `git rev-parse HEAD` on every `*.txt` artifact