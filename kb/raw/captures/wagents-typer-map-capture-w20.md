---
title: Wagents Typer Map Capture W20
tags:
  - kb
  - raw
  - wagents
aliases:
  - Wagents typer map 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave20-pass3-2026-06-25
---

# Wagents Typer Map Capture W20

Typer application tree from `wagents/cli.py` on 2026-06-25. Complements wave 02 CLI surface capture.

## Root app commands

| Command | Purpose |
|---------|---------|
| `doctor` | Environment/toolchain health (`--format text|json|jsonl`) |
| `validate` | Asset frontmatter and registry validation |
| `install` | Skills CLI install orchestration |
| `package` | Portable skill ZIP packaging |
| `readme` | README regeneration / `--check` |

## Nested typer apps

| App | Subcommands area |
|-----|------------------|
| `new` | `skill`, `agent`, `mcp` scaffolds |
| `docs` | init, generate, build, dev, preview, clean |
| `hooks` | hook registry projection |
| `eval` | skill eval management |
| `skills` | search, context, read, sync, doctor |
| `catalog` | Bucket A index authoring |
| `openspec` | init, validate, status, instructions, doctor |
| `opencode` | OpenCode runtime diagnose |
| `grok` | Grok doctor; nested `plannotator` install/sync |
| `self` | wagents self-install doctor |
| `apm` | APM materialize/doctor facade |

## Doctor checks (18)

`python-version`, `uv`, `node`, `npx`, `pnpm`, `node-version`, `pnpm-version`, `docs-deps`, `pre-commit`, `playwright-python`, `playwright-browsers`, `wagents-install-mode`, `wagents-binary`, `repo-discovery`, `telemetry`, `python-tooling-config`, `ruff-tooling`, `ty-tooling`.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Typer tree | `wagents/cli.py` | canonical repo |
| Doctor check names | `uv run wagents doctor --format json` | tool output |