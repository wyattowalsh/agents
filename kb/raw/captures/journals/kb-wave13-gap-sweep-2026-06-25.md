---
title: "Research journal — KB wave 13"
tags:
  - kb
  - raw
  - journal
  - provenance
aliases:
  - "KB wave 13 journal"
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave13-gap-sweep-2026-06-25
original_location: "~/.grok/research/kb-wave13-gap-sweep-2026-06-25.md"
---

# Research journal — KB wave 13

- **Goal:** `goals/kb-research-ingest/goal.md`
- **Wave:** 13 | Theme: Gemini harness and Makefile targets
- **Captured:** 2026-06-25
- **Commit message:** `feat(kb): wave 13 — Gemini harness and Makefile targets`

## G0 brief

Gemini CLI external pointer + Makefile install/dev target matrix.

## Ownership map

| Role | Artifact | Path |
|------|----------|------|
| worker | `makefile-dev-targets-capture-w13` | `kb/raw/captures/makefile-dev-targets-capture-w13.md` |
| worker | `gemini-harness-docs-capture-w13` | `kb/raw/sources/gemini-harness-docs-capture-w13.md` |

## Ingest queue

- `raw`: added 2 sources (`gemini-harness-docs-capture-w13`, `makefile-dev-targets-capture-w13`).

## Capture evidence (excerpts)

### `makefile-dev-targets-capture-w13`

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

### `gemini-harness-docs-capture-w13`

# Gemini Harness Docs Capture W13

| Field | Value |
|-------|-------|
| source_id | `gemini-harness-docs-capture-w13` |
| original_location | `https://github.com/google-gemini/gemini-cli`; `GEMINI.md` bridge in repo root |
| capture_method | official repo pointer + repo bridge read |
| captured_at | 2026-06-25 |

## Summary

Gemini CLI is the official Google terminal agent with MCP support, `GEMINI.md` context files, and non-interactive mode. This repo bridges via root `GEMINI.md` → `@./AGENTS.md` → `@instructions/global.md`, sharing the Antigravity instruction path. Skills install target: `make install-gemini` / `npx skills add ... -a gemini-cli`.

## Repo alignment

| Upstream | Repo surface |
|----------|--------------|
| `GEMINI.md` context | Root `GEMINI.md` import bridge |
| MCP | MCPHub projection via registry (not duplicate Chrome plugin owner) |
| Skills | Skills CLI `gemini-cli` adapter |

## Provenance

| Claim | Source |
|-------|--------|
| URL + GEMINI bridge | `kb/raw/sources/external-harness-docs.md`; `GEMINI.md` |


## Key findings

Derived from command-backed captures above; canonical repo files remain authoritative.

## Metrics

**net-new raw sources: 2**; pages enriched: 3; lint: pass (exit 0).

## Gate status

- G1 research: complete (read-only repo paths / external pointers)
- G2 ingest: captures written under `kb/raw/`
- G3 enrich: wiki/index updates per wave manifest
- G4 audit: `uv run python skills/nerdbot/scripts/kb_lint.py --root kb --fail-on warning` exit 0 before wave commit
