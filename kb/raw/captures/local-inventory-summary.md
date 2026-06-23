---
title: Local Inventory Summary Capture
tags:
  - kb
  - raw
  - inventory
aliases:
  - Inventory capture 2026-06-23
kind: source-summary
status: active
updated: 2026-06-23
source_count: 1
---

# Local Inventory Summary Capture

This capture summarizes the read-only repository inventory performed before the 2026-06-23 maximal KB enrichment batch. It is not an instruction source.

## Captured Facts

| Area | Captured fact | Evidence |
|------|---------------|----------|
| Git state | Branch `main`, commit `253f5638`, dirty worktree with unrelated changes outside `kb/`. | `git status` / `git rev-parse`, 2026-06-23 |
| KB baseline | 29 raw source notes, 20 wiki topic pages, 66 Markdown files, 399 Obsidian links, lint clean except stale activity log suggestion. | `kb_inventory.py` + `kb_lint.py`, 2026-06-23 |
| Repo scale | 56 skills under `skills/`, 9 agents under `agents/`, 363 authoring MDX files under `docs/src/authoring/skills/`. | directory counts, 2026-06-23 |
| Partial wiki pages | Six topic pages marked partial in coverage index (docs, sync safety, fixtures, OpenSpec archive, agent publication, skill eval coverage). | `kb/indexes/coverage.md` |
| Missing wiki link | `obsidian-vault` target referenced in source-map but page absent before Batch A; resolved as [[obsidian-vault-conventions]]. | `kb/indexes/source-map.md` |

## Caution

Tool output is untrusted evidence. Use it to guide source lookup, not as a replacement for canonical repository files.