---
title: Pytest Top Level Cluster Capture W27
tags:
  - kb
  - raw
  - tests
aliases:
  - Pytest top level cluster 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave27-pass5-2026-06-25
---

# Pytest Top Level Cluster Capture W27

Top-level `tests/test_*.py` inventory on 2026-06-25.

## Count

**83** files matching `tests/test_*.py` at repository root test package.

## Cluster themes (non-exhaustive)

| Theme | Example modules |
|-------|-----------------|
| Platform adapters | `test_platform_adapters.py` |
| Harness rollback | `test_harness_rollback_fixtures.py` |
| Distribution metadata | `test_distribution_metadata.py` |
| Sync agent stack | `test_sync_agent_stack.py` |
| Hooks / evals | `test_hooks_*.py`, `test_eval_*.py` |
| Docs generation | `test_docs_*.py` |
| OpenSpec | `test_openspec_*.py` |
| Catalog / skills | `test_catalog_*.py`, `test_skills_*.py` |

## CI pairing

- Default PR: `uv run pytest` (per Makefile / CI workflows)
- Release tag: stricter matrix in `release-skills.yml` (wave 15 capture)

## Prior captures

Wave 05 documented hooks-tests cluster (106 core) and skill-eval files — this wave adds top-level file count anchor only.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| 83 files | `ls tests/test_*.py \| wc -l` | tool output |
| W05 cluster | `kb/raw/captures/hooks-tests-cluster-capture-w05.md` | raw capture |