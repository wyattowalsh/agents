---
title: Developer Commands
tags:
  - kb
  - commands
  - operations
aliases:
  - Repo commands
  - Verification commands
kind: concept
status: active
updated: 2026-05-01
source_count: 7
---

# Developer Commands

## Core Commands

Run these from the repository root unless noted otherwise.

| Purpose | Command | Evidence |
|---------|---------|----------|
| Validate assets | `uv run wagents validate` | `Makefile`, `README.md`, `AGENTS.md` |
| Run tests | `uv run pytest` | `Makefile` |
| Lint Python | `uv run ruff check wagents/ tests/ skills/skill-creator/scripts/` | `Makefile` |
| Type-check | `uv run ty check` | `Makefile`, `pyproject.toml` |
| Audit skills | `uv run python skills/skill-creator/scripts/audit.py --all --format table` | `Makefile` |
| Package skills dry-run | `uv run wagents package --all --dry-run` | `Makefile`, `README.md` |
| Regenerate README | `uv run wagents readme` | `Makefile`, `README.md`, `AGENTS.md` |
| Check README freshness | `uv run wagents readme --check` | `README.md`, `openspec/config.yaml` |
| Generate docs | `uv run wagents docs generate` | `README.md`, `AGENTS.md`, `openspec/config.yaml` |
| Validate OpenSpec | `uv run wagents openspec validate` | `Makefile`, `README.md`, `openspec/config.yaml` |
| Diagnose OpenSpec | `uv run wagents openspec doctor` | `README.md`, `Makefile` |
| Preview skill sync | `uv run wagents skills sync --dry-run` | `README.md`, `AGENTS.md` |
| Package one skill dry-run | `uv run wagents package <name> --dry-run` | `wagents` internals, Makefile |

## Nerdbot KB Commands

| Purpose | Command |
|---------|---------|
| Inventory this KB | `uv run --project skills/nerdbot nerdbot inventory --root ./kb` |
| Lint this KB | `uv run --project skills/nerdbot nerdbot lint --root ./kb --include-unlayered` |
| Show Nerdbot CLI help | `uv run --project skills/nerdbot nerdbot --help` |
| Show Nerdbot modes | `uv run --project skills/nerdbot nerdbot modes` |

## Important Caveat

This page lists verified command definitions, not verified success for every command. See [[known-risks-and-open-gaps]] and [[log]] for commands actually run during this KB batch.

## Related Pages

- [[repository-overview]]
- [[skill-authoring-and-validation]]
- [[wagents-cli-and-automation]]
- [[validation-and-test-coverage]]
- [[docs-generation-and-site]]
- [[openspec-workflow]]
- [[nerdbot]]

## Evidence

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| Make targets wrap validation, tests, lint, typecheck, audit, package, OpenSpec, and README commands. | `kb/raw/sources/pyproject-and-makefile.md`; `kb/raw/extracts/developer-commands-extract.md` | raw source notes | Derived from Makefile. |
| Nerdbot CLI supports inventory and lint under `uv run --project skills/nerdbot nerdbot`. | `kb/raw/sources/nerdbot-skill-contract.md`; `kb/raw/extracts/developer-commands-extract.md` | raw source notes | Derived from Nerdbot README. |
| Generated docs and README commands are generated public surface maintenance commands. | `kb/raw/sources/openspec-config.md` | raw source note | Derived from OpenSpec config. |
| `wagents` command families include validation, docs, packaging, OpenSpec, hooks, evals, install, and sync. | `kb/raw/sources/wagents-internals.md` | raw source note | CLI implementation source. |
| Docs generation and Starlight commands have dedicated implementation and tests. | `kb/raw/sources/docs-site-architecture.md`; `kb/raw/sources/tests-and-validation.md` | raw source notes | Docs evidence. |
