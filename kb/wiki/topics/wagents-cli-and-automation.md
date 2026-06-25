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
updated: 2026-06-25
source_count: 7
---

# Wagents CLI And Automation

## Scope

This page explains the repo-local automation CLI. It does not replace `wagents --help`, implementation tests, or command execution.

## Summary

`wagents` is the repository control CLI for asset validation, scaffolding, docs generation, packaging, install/sync flows, OpenSpec wrappers, hook inspection, and eval inspection. Treat it as the preferred interface for repository operations because its commands encode repo-specific conventions.

The CLI is implemented as a Typer app in `wagents/cli.py`, exposed through the `pyproject.toml` console script `wagents = "wagents.cli:run"` (telemetry-wrapped entry). The root app mounts eleven Typer sub-apps (`docs`, `hooks`, `eval`, `skills`, `catalog`, `openspec`, `opencode`, `grok`, `self`, `apm`, plus `new`) and loads optional plugins from the `wagents.commands` entry-point group via `wagents/plugins/loader.py`. There is no `wagents/commands/` package directory — command modules live in `cli.py`, `docs.py`, `self_cmd.py`, and related packages. Official Typer docs support the explicit `typer.Typer()` and `@app.command()` pattern used by the repo, while local code defines the real command surface.

For package checks, use `uv run wagents package <name> --dry-run` for one skill or `uv run wagents package --all --dry-run` for the whole set. Avoid documenting bare `uv run wagents package --dry-run` as a valid standalone check.

Hooks and evals deserve separate attention from generic CLI coverage: `wagents hooks` surfaces portable hook registry checks, while `wagents eval` surfaces skill evaluation validation and coverage. Use [[hooks-evals-control-plane]] for the runtime/regression split.

## Evidence

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| `wagents` is exposed through `wagents.cli:run` (telemetry wrapper). | `kb/raw/sources/wagents-internals.md`; `kb/raw/captures/wagents-cli-surface-capture-w02.md` | raw source note + capture | `pyproject.toml` `[project.scripts]`. |
| The command surface covers validate, docs, skills, OpenSpec, package, hooks, and evals. | `kb/raw/sources/wagents-internals.md`; `kb/raw/sources/pyproject-and-makefile.md` | raw source notes | Use `--help` for exact flags. |
| Typer supports explicit app and command decorator patterns. | `kb/raw/sources/external-tooling-docs.md` | external source note | Context only; local code is authoritative. |
| Hook and eval commands participate in the repo's control-plane surface. | `kb/raw/sources/hooks-evals-control-source.md` | raw source note | Dedicated hooks/evals source. |
| Console entry is `wagents.cli:run`; root app mounts 11 sub-apps and `wagents.commands` plugin discovery. | `kb/raw/captures/wagents-cli-surface-capture-w02.md` | raw capture | 2026-06-25; no `wagents/commands/` tree. |
| `wagents validate` delegates to `scripts/validate/validate_repo.py` with seven collectors; clean JSON run. | `kb/raw/captures/wagents-validate-capture-w02.md` | raw capture | 2026-06-25 `ok: true`, zero errors. |
| `wagents docs` exposes nine subcommands; `docs generate --check` reports artifacts up to date. | `kb/raw/captures/wagents-docs-cli-capture-w02.md` | raw capture | 2026-06-25 tool capture. |

## Related

- [[developer-commands]]
- [[validation-and-test-coverage]]
- [[docs-generation-and-site]]
- [[openspec-workflow]]
- [[hooks-evals-control-plane]]
