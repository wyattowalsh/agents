---
title: Wagents Docs CLI Capture W02
tags:
  - kb
  - raw
  - wagents
  - docs
aliases:
  - Wagents docs CLI 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave02-wagents-2026-06-25
---

# Wagents Docs CLI Capture W02

Read-only capture from `wagents/docs.py` and `uv run wagents docs --help` on 2026-06-25. Not an instruction source.

## Captured Facts

| Fact | Value | Source |
|------|-------|--------|
| Typer sub-app | `docs_app = typer.Typer(help="Documentation site management")` mounted as `wagents docs` | `wagents/docs.py` |
| Subcommands (9) | `init`, `generate`, `dev`, `build`, `preview`, `research`, `lint`, `compose`, `clean` | `wagents docs --help` |
| Generate stale gate | `docs generate --check` exits 1 with reasons when MDX/index artifacts drift | `docs.py` `docs_generate()` |
| Generate options | `--include-drafts`, `--include-installed/--no-installed` | `docs.py` |
| Research command | batch planning, `--seed-from-repo`, `--seed-from-config`, `--validate-artifacts`, `--emit-waves` | `docs.py` `docs_research()` |
| Lint command | verbosity regression lint; `--strict`, `--baseline/--no-baseline`, `--format text|json` | `docs.py` `docs_lint()` → `wagents/docs_lint.py` |
| Compose command | surfaces `skills|agents|mcp|hooks|configs|all`; `--apply`, upgrade/regen flags | `docs.py` + `wagents/docs_compose*.py` |
| Dev/build/preview | run `pnpm dev|build|preview` in `docs/` after generate | `docs.py` |
| 2026-06-25 generate check | `Generated docs artifacts are up to date` (exit 0) | `wagents docs generate --check` |

## Quoted help excerpt

> `generate  Generate MDX content pages from repo assets.`

> `compose   Track and emit orchestrator waves for composed catalog pages.`

## Interpretation

Docs automation is a first-class Typer subtree, not inlined in `cli.py`. Generation and compose paths own MDX freshness; `research` and `compose` coordinate orchestrator batching; `lint` guards verbosity regressions against `planning/manifests/docs-verbosity-baseline.json`.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Subcommand surface | `wagents/docs.py` | canonical repo path |
| Help listing | `uv run wagents docs --help` | tool capture |
| Generate check status | `uv run wagents docs generate --check` | tool capture |