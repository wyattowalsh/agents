---
title: UV Llms Index Extract W11
tags:
  - kb
  - extract
  - uv
  - tooling
kind: extract
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave11-gap-sweep-2026-06-25
---

# UV Llms Index Extract W11

Normalized extract from `https://docs.astral.sh/uv/llms.txt` fetched 2026-06-25. External evidence only; repo `pyproject.toml` and `Makefile` remain authoritative for commands.

## Index highlights

| Section | Representative paths |
|---------|---------------------|
| Getting started | `getting-started/features`, `installation`, `first-steps` |
| Guides | `guides/projects`, `guides/scripts`, `guides/tools`, `guides/package` |
| Integrations | `guides/integration/github`, `guides/integration/pre-commit`, `guides/integration/docker` |
| Projects | `concepts/projects/dependencies`, `concepts/projects/sync`, `concepts/projects/workspaces` |
| Pip interface | `pip/packages`, `pip/compile`, `pip/environments` |
| Reference | `reference/cli`, `reference/settings`, `reference/environment` |

## Quoted guidance

> uv includes both a pip-compatible CLI (prepend `uv` to a pip command, e.g., `uv pip install ruff`) and a first-class project interface (e.g., `uv add ruff`) complete with lockfiles and workspace support.

> When fetching documentation, use explicit `index.md` paths for directories, e.g., `https://docs.astral.sh/uv/concepts/projects/dependencies/index.md`.

## Repo alignment notes

| Upstream concept | Repo surface |
|------------------|--------------|
| `uv run` project commands | CI `.github/actions/setup-uv` + `uv run wagents`, `uv run pytest`, `uv run ruff check` |
| Workspaces | `[tool.uv.workspace] members = ["mcp/mcphub"]` in `pyproject.toml` |
| Dev dependency groups | `[dependency-groups] dev` pins `ruff>=0.11`, `ty==0.0.52`, `pytest>=8` |

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| llms.txt section map | `https://docs.astral.sh/uv/llms.txt` | external fetch |
| Workspace member | `pyproject.toml` `[tool.uv.workspace]` | canonical repo |