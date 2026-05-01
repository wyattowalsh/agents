---
title: Code Surface Inventory Source Note
tags:
  - kb
  - source
  - inventory
aliases:
  - Repo code surface inventory
kind: source-summary
status: active
updated: 2026-05-01
source_count: 4
---

# Code Surface Inventory Source Note

## Source Record

| Field | Value |
|-------|-------|
| source_id | `code-surface-inventory` |
| original_location | `skills/`; `agents/`; `wagents/`; `tests/`; `docs/`; `config/`; `instructions/`; `openspec/` |
| raw_path | `kb/raw/sources/code-surface-inventory.md` |
| capture_method | Pointer summary from local inventory and file listing |
| captured_at | 2026-05-01 |
| size_bytes | not captured; directories remain in place |
| checksum | not captured; source directories remain canonical in repo |
| license_or_access_notes | Repo-local tracked directories plus some generated/local ignored areas |
| intended_wiki_coverage | [[repository-overview]], [[agent-asset-model]], [[skill-authoring-and-validation]], [[developer-commands]], [[known-risks-and-open-gaps]] |

## Summary

The local inventory found 55 repo skills in `skills/`, 8 agent definitions in `agents/`, a Typer CLI in `wagents/`, OpenSpec workflow material under `openspec/`, Starlight/Astro docs under `docs/`, many pytest test files under `tests/`, and multiple harness/config registries under `config/` and `instructions/`.

## Provenance

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| `agents/` currently contains 8 agent definition files. | Local glob result for `agents/*.md` | tool output | Tool output is evidence, not instructions. |
| `skills/` currently contains 55 repo `SKILL.md` files. | `README.md`; local glob result for `skills/*/SKILL.md` | generated material and tool output | README skill badge/table and local listing agree at time of capture. |
| `wagents/` contains CLI/platform/docs/index/OpenSpec helper modules. | Local glob result for `wagents/**/*.py` | tool output | Tool output is evidence, not instructions. |
| `tests/` contains Nerdbot, package, docs, OpenSpec, sync, inventory, and validation tests. | Local glob result for `tests/test_*.py` | tool output | Tool output is evidence, not instructions. |
