---
title: Pyproject And Makefile Source Note
tags:
  - kb
  - source
aliases:
  - Developer Commands Source
kind: source-summary
status: active
updated: 2026-05-01
source_count: 2
---

# Pyproject And Makefile Source Note

## Source Record

| Field | Value |
|-------|-------|
| source_id | `pyproject-and-makefile` |
| original_location | `pyproject.toml`; `Makefile` |
| raw_path | `kb/raw/sources/pyproject-and-makefile.md` |
| capture_method | Pointer summary from repo-local command/config files |
| captured_at | 2026-05-01 |
| size_bytes | not captured; sources remain in place |
| checksum | not captured; sources remain canonical in repo |
| license_or_access_notes | Repo-local tracked files |
| intended_wiki_coverage | [[developer-commands]], [[repository-overview]] |

## Summary

`pyproject.toml` defines the `wagents` Python project, Python `>=3.13`, Typer/Rich/HTTP dependencies, dev tooling, pytest paths, Ruff settings, Ty configuration, and an empty `uv` workspace member list. `Makefile` exposes install, validation, test, lint, typecheck, audit, package, OpenSpec, and README regeneration targets.

## Provenance

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| The project package is named `wagents` and exposes the `wagents` script. | `pyproject.toml` | canonical material | Project and scripts sections. |
| The Python baseline in project config is `>=3.13`, with Ruff target `py313` and Ty Python version `3.13`. | `pyproject.toml` | canonical material | Project and tooling sections. |
| Make targets wrap `uv run wagents validate`, `uv run pytest`, `uv run ruff check ...`, `uv run ty check`, and OpenSpec commands. | `Makefile` | canonical material | Development section. |
