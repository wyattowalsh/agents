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
updated: 2026-06-25
source_count: 8
---

# Developer Commands

## Core Commands

Run these from the repository root unless noted otherwise.

| Purpose | Command | Evidence |
|---------|---------|----------|
| Validate assets | `uv run wagents validate` or `just validate` | `justfile`, `README.md`, `AGENTS.md` |
| Run tests | `uv run pytest` or `just test` | `justfile` |
| Lint Python | `uv run ruff check` or `just lint` | `justfile` |
| Type-check | `uv run ty check` or `just typecheck` | `justfile`, `pyproject.toml` |
| Audit skills | `uv run python skills/skill-creator/scripts/audit.py --all --format table` or `just audit` | `justfile` |
| Package skills dry-run | `uv run wagents package --all --dry-run` or `just package` | `justfile`, `README.md` |
| Regenerate README | `uv run wagents readme` or `just readme` | `justfile`, `README.md`, `AGENTS.md` |
| Check README freshness | `uv run wagents readme --check` | `README.md`, `openspec/config.yaml` |
| Generate docs | `uv run wagents docs generate` | `README.md`, `AGENTS.md`, `openspec/config.yaml` |
| Validate OpenSpec | `uv run wagents openspec validate` or `just openspec-validate` | `justfile`, `README.md`, `openspec/config.yaml` |
| Diagnose OpenSpec | `uv run wagents openspec doctor` or `just openspec-doctor` | `README.md`, `justfile` |
| Preview skill sync | `uv run wagents skills sync --dry-run` | `README.md`, `AGENTS.md` |
| Package one skill dry-run | `uv run wagents package <name> --dry-run` | `wagents` internals, `justfile` |

## Just Recipes

Common `just` aliases (requires just **≥ 1.52.0**; see `justfile`):

| Purpose | Command |
|---------|---------|
| List recipes | `just` or `just --list` |
| Full Python checks | `just check-python` |
| Sync projection drift | `just sync-check` |
| Workflow lint (local) | `just ci-check` |
| Install skills to a harness | `just install-claude`, `just install-cursor`, `just install-codex`, etc. |
| Install one skill to all agents | `just install-skill --skill <name>` |
| MCPHub control plane | `just mcphub-up`, `just mcphub-doctor`, `just mcphub-smoke` |

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
| Just recipes wrap validation, tests, lint, typecheck, audit, package, OpenSpec, README, MCPHub, and skills install commands. | `justfile` | canonical repo | Replaced Makefile aliases (2026). |
| Nerdbot CLI supports inventory and lint under `uv run --project skills/nerdbot nerdbot`. | `kb/raw/sources/nerdbot-skill-contract.md`; `kb/raw/extracts/developer-commands-extract.md` | raw source notes | Derived from Nerdbot README. |
| Generated docs and README commands are generated public surface maintenance commands. | `kb/raw/sources/openspec-config.md` | raw source note | Derived from OpenSpec config. |
| `wagents` command families include validation, docs, packaging, OpenSpec, hooks, evals, install, and sync. | `kb/raw/sources/wagents-internals.md` | raw source note | CLI implementation source. |
| Docs generation and Starlight commands have dedicated implementation and tests. | `kb/raw/sources/docs-site-architecture.md`; `kb/raw/sources/tests-and-validation.md` | raw source notes | Docs evidence. |
| Just install targets per harness plus dev/ci-check/sync-check aliases. | `justfile` | canonical repo | Migrated from Makefile. |
