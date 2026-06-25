---
title: Repository Inventory Capture W15
tags:
  - kb
  - raw
  - inventory
aliases:
  - Repo inventory 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave15-pass2-2026-06-25
---

# Repository Inventory Capture W15

Explicit-path inventory on 2026-06-25 (no repo-wide globs).

## Cardinality

| Surface | Count | Method |
|---------|-------|--------|
| `skills/` top-level dirs | **56** | `ls skills \| wc -l` |
| `agents/*.md` definitions | **9** | `ls agents \| wc -l` (includes README.md) |
| `config/mcp-registry.json` servers | **33** | `json.load` key count |
| Catalog authoring MDX | **363** | prior wave 06 capture |
| Harness surfaces (registry) | **19** | prior wave 03 capture |

## Agent filenames

`code-reviewer`, `docs-writer`, `orchestrator`, `performance-profiler`, `planner`, `release-manager`, `researcher`, `security-auditor` (+ `README.md` index).

## Interpretation

Public README/catalog counts may lag; use this capture + `wagents validate` for session claims. MCP docs badge drift (15 vs 33) remains a known repo fix — see [[known-risks-and-open-gaps]].

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Counts | explicit shell + JSON parse | tool capture |
| Prior catalog/harness | `kb/raw/captures/catalog-authoring-mdx-capture-w06.md`; `kb/raw/captures/harness-surface-registry-capture-w03.md` | raw captures |