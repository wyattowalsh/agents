---
title: Wagents Validate Capture W02
tags:
  - kb
  - raw
  - wagents
  - validate
aliases:
  - Wagents validate 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave02-wagents-2026-06-25
---

# Wagents Validate Capture W02

Read-only capture from `wagents validate`, `scripts/validate/validate_repo.py`, and collector modules on 2026-06-25. Not an instruction source.

## Captured Facts

| Fact | Value | Source |
|------|-------|--------|
| CLI command | `wagents validate` | `wagents/cli.py` `@app.command()` |
| Delegation target | `scripts/validate/validate_repo.py` via `resolve_repo_script` | `cli.py` `validate()` |
| Output formats | `--format text|json|jsonl` | CLI + `validate_repo.py` argparse |
| Collector modules | skills, agents, mcp, hooks, paths, mcp_registry, quarantine (7) | `scripts/validate/collectors/` |
| Merge function | `collect_repo_errors()` concatenates all collector error lists | `validate_repo.py` |
| Exit semantics | return code 1 when any errors; 0 when clean | `validate_repo.py` `main()` |
| 2026-06-25 JSON run | `ok: true`, `error_count: 0`, message `All validations passed` | `wagents validate --format json` |

## Quoted CLI excerpt

> `"ok": true, "error_count": 0, "errors": [], "message": "All validations passed"`

## Interpretation

`wagents validate` is a thin Typer wrapper over the repo validation toolkit under `scripts/validate/`. It is the primary asset gate for skills, agents, MCP servers, hooks, path portability, MCP registry rows, and quarantine policy — distinct from `wagents hooks validate` and `wagents eval validate`, which target hook scripts and eval JSON respectively.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Delegation and collectors | `wagents/cli.py`, `scripts/validate/validate_repo.py` | canonical repo paths |
| Collector inventory | `scripts/validate/collectors/*.py` | canonical repo paths |
| Live pass status | `uv run wagents validate --format json` | tool capture |