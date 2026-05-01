---
title: Tests And Validation
tags:
  - kb
  - source
  - tests
aliases:
  - Test suite source
kind: source-summary
status: active
updated: 2026-05-01
source_count: 1
---

# Tests And Validation

## Source Record

| Field | Value |
|-------|-------|
| source_id | `tests-and-validation` |
| original_location | `tests/test_cli_integration.py`; `tests/test_openspec_cli.py`; `tests/test_docs.py`; `tests/test_readme.py`; `tests/test_package.py`; `tests/test_skill_index.py`; `tests/test_installed_inventory.py`; `tests/test_external_skills.py`; `tests/test_catalog.py`; `tests/test_hooks_cli.py`; `tests/test_eval_cli.py`; `tests/test_nerdbot*.py` |
| raw_path | `kb/raw/sources/tests-and-validation.md` |
| capture_method | repo-local pointer summary from read-only inspection |
| captured_at | 2026-05-01 |
| size_bytes | pointer summary only |
| checksum | not captured |
| license_or_access_notes | repo-local canonical material |
| intended_wiki_coverage | [[validation-and-test-coverage]], [[developer-commands]], [[known-risks-and-open-gaps]] |

## Summary

The pytest suite maps directly to major repo contracts. CLI integration tests cover command availability and behavior. OpenSpec tests cover wrapper behavior, telemetry defaults, JSON wrapping, and archive/update flows. Docs and README tests protect generated outputs. Package tests protect portable ZIP behavior and portability warnings. Skill index/inventory/external-skill tests protect skill discovery and sync inputs. Nerdbot tests protect KB workflow contracts, path safety, lint/inventory, query, graph, replay, and watch behavior.

## Provenance

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| Tests are organized around CLI, docs, packaging, OpenSpec, skill inventory, hooks/evals, and Nerdbot. | `tests/` | canonical material | Source map for future validation work. |
| Full CI status was not established by this KB batch. | local execution record | activity evidence | Only Nerdbot inventory/lint is run here. |
