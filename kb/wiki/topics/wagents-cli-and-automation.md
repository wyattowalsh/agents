---
title: Wagents CLI And Automation
tags:
  - kb
  - wagents
  - cli
aliases:
  - wagents CLI
kind: concept
status: active
updated: 2026-05-01
source_count: 4
---

# Wagents CLI And Automation

## Scope

This page explains the repo-local automation CLI. It does not replace `wagents --help`, implementation tests, or command execution.

## Summary

`wagents` is the repository control CLI for asset validation, scaffolding, docs generation, packaging, install/sync flows, OpenSpec wrappers, hook inspection, and eval inspection. Treat it as the preferred interface for repository operations because its commands encode repo-specific conventions.

The CLI is implemented as a Typer app in `wagents/cli.py`, exposed through the `pyproject.toml` console script `wagents = "wagents.cli:app"`. Official Typer docs support the explicit `typer.Typer()` and `@app.command()` pattern used by the repo, while local code defines the real command surface.

For package checks, use `uv run wagents package <name> --dry-run` for one skill or `uv run wagents package --all --dry-run` for the whole set. Avoid documenting bare `uv run wagents package --dry-run` as a valid standalone check.

Hooks and evals deserve separate attention from generic CLI coverage: `wagents hooks` surfaces portable hook registry checks, while `wagents eval` surfaces skill evaluation validation and coverage. Use [[hooks-evals-control-plane]] for the runtime/regression split.

## Evidence

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| `wagents` is exposed through `wagents.cli:app`. | `kb/raw/sources/wagents-internals.md` | raw source note | Derived from `pyproject.toml`. |
| The command surface covers validate, docs, skills, OpenSpec, package, hooks, and evals. | `kb/raw/sources/wagents-internals.md`; `kb/raw/sources/pyproject-and-makefile.md` | raw source notes | Use `--help` for exact flags. |
| Typer supports explicit app and command decorator patterns. | `kb/raw/sources/external-tooling-docs.md` | external source note | Context only; local code is authoritative. |
| Hook and eval commands participate in the repo's control-plane surface. | `kb/raw/sources/hooks-evals-control-source.md` | raw source note | Dedicated hooks/evals source. |

## Related

- [[developer-commands]]
- [[validation-and-test-coverage]]
- [[docs-generation-and-site]]
- [[openspec-workflow]]
- [[hooks-evals-control-plane]]
