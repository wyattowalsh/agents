---
title: Makefile Dev Targets Capture W13
tags:
  - kb
  - raw
  - makefile
aliases:
  - Makefile targets 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave13-gap-sweep-2026-06-25
---

# Makefile Dev Targets Capture W13

Read-only capture from `Makefile` on 2026-06-25.

## Install targets (Skills CLI)

| Target | Agent flag |
|--------|------------|
| `install` | `--agent '*'` |
| `install-claude` | `claude-code` |
| `install-cursor` | `cursor` |
| `install-copilot` | `github-copilot` |
| `install-gemini` | `gemini-cli` |
| `install-codex` | `codex` |
| `install-opencode` | `opencode` |
| `install-crush` | `crush` |
| `install-antigravity` | `antigravity` |

Source repo: `github:wyattowalsh/agents` (`REPO` variable).

## Development targets

| Target | Command |
|--------|---------|
| `validate` | `uv run wagents validate` |
| `test` | `uv run pytest` |
| `lint` | `uv run ruff check` |
| `typecheck` | `uv run ty check` |
| `ci-check` | actionlint + workflow-analyzer |
| `docs-build` | `uv run wagents docs build` |
| `sync-check` | `uv run python scripts/sync_agent_stack.py --check --targets all` |

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Target table | `Makefile` | canonical repo |
| Prior aliases | `kb/raw/sources/pyproject-and-makefile.md` | raw source note |