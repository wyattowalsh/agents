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

## Commands

| Step | Command |
|------|---------|
| Inventory | `uv run python skills/nerdbot/scripts/kb_inventory.py --root kb` |
| Lint | `uv run python skills/nerdbot/scripts/kb_lint.py --root kb --fail-on warning` |
| Partials | `rg -F '| partial |' kb/indexes/coverage.md` → 0 matches |
| Waves | `rg -c '^### \[' kb/activity/log.md` ≥ 10 |
| Repo-map | cross-check primary table paths in `kb/raw`, `kb/wiki`, `kb/indexes/source-map.md` |
| Wave scope | last 3 `feat(kb): wave` commits touch `kb/**` only |
| Closure | `bash kb/activity/goal-verify.sh` → `goal-hygiene-check.sh` → `goal-capture-template.sh` |

## Acceptance gates

- `issue_count: 0` from kb_lint JSON summary
- `source_count` in `kb/indexes/source-map.md` aligned with data rows (see verification-summary.txt)
- Scratch `verification_tree` must equal `git rev-parse HEAD` on every `*.txt` artifact