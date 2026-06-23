---
title: Scripts And Validation Tooling
tags:
  - kb
  - source
  - validation
aliases:
  - Scripts validation source
kind: source-summary
status: active
updated: 2026-06-23
source_count: 1
---

# Scripts And Validation Tooling

## Source Record

| Field | Value |
|-------|-------|
| source_id | `scripts-validation-tooling` |
| original_location | `scripts/validate/validate_repo.py`; `scripts/validate/collectors/`; `scripts/sync_agent_stack.py`; `scripts/check_agent_stack.py`; `scripts/validate_codex_config.py` |
| raw_path | `kb/raw/sources/scripts-validation-tooling-source.md` |
| capture_method | repo-local pointer summary from read-only research |
| captured_at | 2026-06-23 |
| size_bytes | pointer summary only |
| checksum | not captured |
| license_or_access_notes | repo-local canonical material |
| intended_wiki_coverage | [[scripts-and-validation-tooling]], [[validation-and-test-coverage]], [[sync-transaction-safety]] |

## Summary

`wagents validate` delegates to `scripts/validate/validate_repo.py`, which aggregates collectors for skills (asset_toolkit), agents (agent-conventions subprocess), MCP, hooks, path portability, MCP registry contributor policy, and quarantine (dual-read of catalog index + legacy external-skills MD against security quarantine register).

`scripts/sync_agent_stack.py` is the canonical sync engine with `--check`/`--apply` modes. `scripts/check_agent_stack.py` is a thin wrapper calling `sync_main(["--check", "--targets", "all"])`.

`scripts/validate_codex_config.py` exists for Codex config schema validation but is not wired into CI or pre-commit as of 2026-06-23. Hook scripts (`hooks/lint-check.sh` etc.) use narrower allowlists than `pyproject.toml` ruff/ty scope.

## Provenance

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| validate_repo aggregator and collectors. | `scripts/validate/validate_repo.py`; `collectors/*.py` | canonical material | Text/json/jsonl output |
| Sync check wrapper. | `scripts/check_agent_stack.py`; `scripts/sync_agent_stack.py` | canonical material | Drift detection |
| Orphaned Codex schema validator. | `scripts/validate_codex_config.py` | canonical material | Not in CI |
| Tooling scope differences hooks vs pyproject. | `pyproject.toml`; `hooks/lint-check.sh` | canonical material | Drift vector |

## Planned wiki coverage

| Topic | Status |
|-------|--------|
| [[scripts-and-validation-tooling]] | primary synthesis |