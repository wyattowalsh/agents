---
title: Wagents CLI Surface Capture W02
tags:
  - kb
  - raw
  - wagents
  - cli
aliases:
  - Wagents CLI surface 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave02-wagents-2026-06-25
---

# Wagents CLI Surface Capture W02

Read-only capture from `wagents/cli.py`, `pyproject.toml`, and `uv run wagents --help` on 2026-06-25. Not an instruction source.

## Captured Facts

| Fact | Value | Source |
|------|-------|--------|
| Console script | `wagents = "wagents.cli:run"` | `pyproject.toml` `[project.scripts]` |
| Root Typer app | `app = typer.Typer(...)` in `wagents/cli.py` | canonical repo path |
| Sub-apps mounted on root | `new`, `docs`, `hooks`, `eval`, `skills`, `catalog`, `openspec`, `opencode`, `grok` (+ `plannotator`), `self`, `apm` | `cli.py` `add_typer` calls |
| Top-level commands (help) | `doctor`, `validate`, `install`, `update`, `package`, `readme` + 11 sub-app groups | `wagents --help` |
| Plugin extension group | `wagents.commands` entry points via `load_command_plugins(app)` | `wagents/plugins/loader.py` |
| Physical `wagents/commands/` package | **absent** — commands live in `cli.py`, `docs.py`, `self_cmd.py`, platform modules | repo tree |
| Structured output formats | `text`, `json`, `jsonl` on many commands (`--format`) | `wagents/output.py`, CLI options |
| Repo root discovery | `--repo-root` / `WAGENTS_REPO_ROOT` env via `wagents/context.py` | `wagents --help` |
| Doctor checks (sample run) | 18 checks, 17 ok | `wagents doctor --format json` |

## Quoted help excerpt

> `CLI for managing centralized AI agent assets`

> Commands include `doctor`, `validate`, `install`, `update`, `package`, `readme`, `new`, `docs`, `hooks`, `eval`, `skills`, `catalog`, `openspec`, `opencode`, `grok`, `self`, `apm`.

## Interpretation

`wagents` is the repo automation façade: Typer sub-apps partition docs, hooks, evals, skills inventory, catalog authoring, OpenSpec, platform doctors, self-install, and APM materialization. Third-party commands can register through the `wagents.commands` setuptools entry-point group without adding a `wagents/commands/` tree.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Entry point and sub-app layout | `wagents/cli.py`, `pyproject.toml` | canonical repo paths |
| Help command list | `uv run wagents --help` | tool capture |
| Plugin loader | `wagents/plugins/loader.py` | canonical repo path |
| Doctor counts | `uv run wagents doctor --format json` | tool capture |