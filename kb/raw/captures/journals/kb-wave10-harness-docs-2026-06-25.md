---
title: "Research journal — KB wave 10"
tags:
  - kb
  - raw
  - journal
  - provenance
aliases:
  - "KB wave 10 journal"
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave10-harness-docs-2026-06-25
original_location: "~/.grok/research/kb-wave10-harness-docs-2026-06-25.md"
---

# Research journal — KB wave 10

- **Goal:** `goals/kb-research-ingest/goal.md`
- **Wave:** 10 | Theme: external harness doc pointers
- **Captured:** 2026-06-25
- **Commit message:** `feat(kb): wave 10 — external harness doc pointers`

## G0 brief

Full-capture pointers for OpenCode, Cursor, and GitHub Copilot harness docs (explicit URLs; no globs).

## Ownership map

| Role | Artifact | Path |
|------|----------|------|
| worker | `copilot-harness-docs-capture-w10` | `kb/raw/sources/copilot-harness-docs-capture-w10.md` |
| worker | `cursor-docs-capture-w10` | `kb/raw/sources/cursor-docs-capture-w10.md` |
| worker | `opencode-docs-capture-w10` | `kb/raw/sources/opencode-docs-capture-w10.md` |

## Ingest queue

- `raw`: added 3 sources (`opencode-docs-capture-w10`, `cursor-docs-capture-w10`, `copilot-harness-docs-capture-w10`).

## Capture evidence (excerpts)

### `copilot-harness-docs-capture-w10`

# Copilot Harness Docs Capture W10

| Field | Value |
|-------|-------|
| source_id | `copilot-harness-docs-capture-w10` |
| original_location | `https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions`; `https://docs.github.com/en/copilot/how-tos/provide-context/use-mcp/use-the-github-mcp-server` |
| capture_method | official GitHub docs pointer |
| captured_at | 2026-06-25 |

## Summary

GitHub Copilot docs describe repository custom instructions and GitHub MCP Server usage. Repo generates `.github/copilot-instructions.md` and scoped rules from `instructions/copilot-global.md` via sync tooling.

## Provenance

| Claim | Source |
|-------|--------|
| URL list | `kb/raw/sources/external-harness-docs.md` |
| Generated surfaces | `kb/raw/sources/config-registries-and-sync.md` |

### `cursor-docs-capture-w10`

# Cursor Docs Capture W10

| Field | Value |
|-------|-------|
| source_id | `cursor-docs-capture-w10` |
| original_location | `https://docs.cursor.com/llms.txt` |
| capture_method | official docs index pointer |
| captured_at | 2026-06-25 |

## Summary

Cursor publishes an llms.txt documentation index for IDE agent features, rules, and MCP. Repo `AGENTS.md`, `.cursor/rules/`, and `wagents/platforms/cursor.py` define managed sync and agent overlays.

## Provenance

| Claim | Source |
|-------|--------|
| Index URL | `kb/raw/sources/external-harness-docs.md` |
| Adapter | `kb/raw/captures/platform-adapters-fleet-capture-w08.md` |

### `opencode-docs-capture-w10`

# OpenCode Docs Capture W10

| Field | Value |
|-------|-------|
| source_id | `opencode-docs-capture-w10` |
| original_location | `https://opencode.ai/docs/config/`; `https://opencode.ai/docs/mcp-servers/`; `https://opencode.ai/docs/plugins/` |
| capture_method | official docs URL pointer (context only) |
| captured_at | 2026-06-25 |

## Summary

OpenCode upstream docs cover project config, MCP server wiring, and npm plugin arrays. Repo `opencode.json`, `instructions/opencode-global.md`, and `wagents/platforms/opencode.py` override for managed policy.

## Provenance

| Claim | Source |
|-------|--------|
| URL list | `kb/raw/sources/external-harness-docs.md` |
| Repo policy | `kb/raw/sources/opencode-policy-and-runtime-plugins.md` |


## Key findings

Derived from command-backed captures above; canonical repo files remain authoritative.

## Metrics

**net-new raw sources: 3**; pages enriched: 2; lint: pass.

## Gate status

- G1 research: complete (read-only repo paths / external pointers)
- G2 ingest: captures written under `kb/raw/`
- G3 enrich: wiki/index updates per wave manifest
- G4 audit: `uv run python skills/nerdbot/scripts/kb_lint.py --root kb --fail-on warning` exit 0 before wave commit
