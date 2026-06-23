---
title: MCPHub Control Plane
tags:
  - kb
  - source
  - mcp
  - mcphub
aliases:
  - MCPHub source
kind: source-summary
status: active
updated: 2026-06-23
source_count: 1
---

# MCPHub Control Plane

## Source Record

| Field | Value |
|-------|-------|
| source_id | `mcphub-control-plane` |
| original_location | `mcp/mcphub/README.md`; `config/mcp-registry.json`; `mcp/mcphub/mcp_settings.json`; `scripts/mcphub/`; `scripts/sync_agent_stack.py`; `wagents/platforms/base.py`; `AGENTS.md` §2.6 |
| raw_path | `kb/raw/sources/mcphub-control-plane-source.md` |
| capture_method | repo-local pointer summary from read-only research |
| captured_at | 2026-06-23 |
| size_bytes | pointer summary only |
| checksum | not captured |
| license_or_access_notes | repo-local canonical material; secrets only in `.env.mcphub` |
| intended_wiki_coverage | [[mcphub-control-plane]], [[mcp-configuration-and-safety]], [[plugin-and-mcp-ownership]] |

## Summary

When `mcphub.enabled` is true in `config/mcp-registry.json`, MCPHub (`@samanhappy/mcphub` via `scripts/mcphub/`) owns local MCP server processes on `http://127.0.0.1:46683`. Clients connect to MCPHub group or server endpoints instead of launching each server directly. The registry is the canonical server definition surface; `mcp/mcphub/mcp_settings.json` is the tracked, secret-free derived settings file.

Groups include `harness-safe`, `research`, `reasoning`, `code`, `browser`, `personal`, and `experimental`. Client projections differ per harness (HTTP vs `remote-stdio.sh` + `mcp-remote`). Bearer auth stays enabled; tracked files use `${ENV_VAR}` placeholders only.

First-party MCP authoring remains in `mcp/<name>/` (FastMCP conventions). Today only `mcp/mcphub/` exists as first-party; `mcp/servers/` is gitignored local checkout area.

## Provenance

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| Registry is SSOT; MCPHub owns processes when enabled. | `mcp/mcphub/README.md`; `AGENTS.md` | canonical material | Control-plane model |
| Settings must stay secret-free; validate enforces parity. | `scripts/mcphub/validate_settings.py` | canonical material | Routing + group checks |
| Projections rendered by sync_agent_stack + platforms. | `scripts/sync_agent_stack.py`; `wagents/platforms/base.py` | canonical material | Per-harness shapes |
| One-owner-per-harness for chrome-devtools etc. | `config/mcp-registry.json`; `config/plugin-extension-registry.json` | canonical material | Suppress duplicate projection |

## Planned wiki coverage

| Topic | Status |
|-------|--------|
| [[mcphub-control-plane]] | primary synthesis |
| [[mcp-configuration-and-safety]] | enrich cross-link |