---
title: Wagents Internals
tags:
  - kb
  - source
  - wagents
aliases:
  - wagents CLI source
kind: source-summary
status: active
updated: 2026-05-01
source_count: 1
---

# Wagents Internals

## Source Record

| Field | Value |
|-------|-------|
| source_id | `wagents-internals` |
| original_location | `pyproject.toml`; `wagents/__init__.py`; `wagents/cli.py`; `wagents/docs.py`; `wagents/catalog.py`; `wagents/rendering.py`; `wagents/site_model.py`; `Makefile`; `tests/test_cli_integration.py` |
| raw_path | `kb/raw/sources/wagents-internals.md` |
| capture_method | repo-local pointer summary from read-only inspection |
| captured_at | 2026-05-01 |
| size_bytes | pointer summary only |
| checksum | not captured |
| license_or_access_notes | repo-local canonical material |
| intended_wiki_coverage | [[wagents-cli-and-automation]], [[developer-commands]], [[validation-and-test-coverage]] |

## Summary

`wagents` is the repository automation CLI. The package entry point is `wagents = "wagents.cli:app"`, with Python `>=3.13` and Typer/Rich/httpx/loguru dependencies. The root app exposes subapps for `new`, `docs`, `hooks`, `eval`, `skills`, and `openspec`.

Important command surfaces include `doctor`, `validate`, `new skill|agent|mcp`, `install`, `update`, `skills index/search/read/context/doctor/sync`, `openspec doctor/init/update/validate/status/instructions/schemas/archive`, `readme`, `docs init/generate/dev/build/preview/clean`, `package`, `hooks list/validate`, and `eval list/validate/coverage`.

The `package` command delegates to the skill-creator packaging script. Prefer `wagents package <name> --dry-run` or `wagents package --all --dry-run`; do not document bare `wagents package --dry-run` as sufficient because the implementation requires either a skill name or `--all`.

## Provenance

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| `wagents` is a Typer CLI exposed through `wagents.cli:app`. | `pyproject.toml`; `wagents/cli.py` | canonical material | Confirmed by read-only source inspection. |
| CLI subapps cover scaffolding, docs, hooks, evals, skills, and OpenSpec. | `wagents/cli.py` | canonical material | Subagent inventory mapped command groups. |
| Package dry-run requires a skill name or `--all`. | `wagents/cli.py`; `skills/skill-creator/scripts/package.py`; `tests/test_package.py` | canonical material | Documented as a command gotcha. |
