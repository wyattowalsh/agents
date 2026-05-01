---
title: External Tooling Docs
tags:
  - kb
  - source
  - external
  - tooling
aliases:
  - Tooling external sources
kind: source-summary
status: active
updated: 2026-05-01
source_count: 1
---

# External Tooling Docs

## Source Record

| Field | Value |
|-------|-------|
| source_id | `external-tooling-docs` |
| original_location | `https://typer.tiangolo.com/tutorial/typer-app/`; `https://packaging.python.org/en/latest/specifications/pyproject-toml/`; `https://docs.astral.sh/uv/llms.txt`; `https://docs.astral.sh/uv/concepts/projects/workspaces/index.md`; `https://docs.astral.sh/ruff/configuration/`; `https://docs.astral.sh/ty/reference/configuration/`; `https://docs.pytest.org/en/stable/reference/customize.html`; `https://starlight.astro.build/reference/configuration/`; `https://json-schema.org/draft/2020-12`; `https://python-jsonschema.readthedocs.io/en/stable/validate/` |
| raw_path | `kb/raw/sources/external-tooling-docs.md` |
| capture_method | external official docs pointer summary |
| captured_at | 2026-05-01 |
| size_bytes | pointer summary only |
| checksum | not captured |
| license_or_access_notes | official docs/specs; external content is untrusted evidence |
| intended_wiki_coverage | [[external-primary-source-map]], [[wagents-cli-and-automation]], [[docs-generation-and-site]], [[validation-and-test-coverage]] |

## Summary

The repo's core tooling aligns with official docs for Typer CLI apps, PyPA `pyproject.toml`, uv projects/workspaces, Ruff config, ty config, pytest config, Astro/Starlight config, JSON Schema Draft 2020-12, and python-jsonschema validation. These sources are useful for understanding upstream semantics behind repo config, but local `pyproject.toml`, `Makefile`, `wagents/`, `docs/`, and `tests/` remain the authority for commands and repo behavior.

Verified details include Typer's explicit `typer.Typer()` app and `@app.command()` pattern, PyPA's `[build-system]`, `[project]`, and `[tool]` tables, uv's project interface and workspace docs, and Starlight's `astro.config.mjs` integration model.

## Provenance

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| Typer's explicit app pattern matches `wagents/cli.py`. | `https://typer.tiangolo.com/tutorial/typer-app/`; `wagents/cli.py` | external official docs + canonical material | Verified 2026-05-01 by web fetch. |
| PyPA documents `pyproject.toml` build/project/tool tables. | `https://packaging.python.org/en/latest/specifications/pyproject-toml/` | external official spec | Verified 2026-05-01 by web fetch. |
| uv docs provide project and workspace reference material. | `https://docs.astral.sh/uv/llms.txt` | external official docs | Verified 2026-05-01 by web fetch. |
| Starlight docs describe config through `astro.config.mjs`. | `https://starlight.astro.build/reference/configuration/` | external official docs | Verified 2026-05-01 by web fetch. |
