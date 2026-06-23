---
title: MCPHub Control Plane
tags:
  - kb
  - mcp
  - mcphub
aliases:
  - MCPHub local control plane
kind: concept
status: active
updated: 2026-06-23
source_count: 2
---

# MCPHub Control Plane

## Summary

MCPHub is the preferred local MCP control plane when enabled in `config/mcp-registry.json`. Edit servers once in the registry, keep `mcp/mcphub/mcp_settings.json` secret-free and validated, and let clients connect to MCPHub on `http://127.0.0.1:46683` via group or server endpoints instead of launching duplicate standalone processes.

## Why it matters

- Reduces per-harness MCP process sprawl and centralizes auth, routing, and groups.
- `harness-safe` is the primary shared group for managed harness surfaces.
- One-owner-per-harness rules still apply (especially Chrome DevTools).

## Current shape

| Component | Role |
|-----------|------|
| `config/mcp-registry.json` | Canonical server defs, groups, client projections, ownership |
| `mcp/mcphub/mcp_settings.json` | Tracked derived settings (placeholders only) |
| `scripts/mcphub/` | Launch, doctor, validate, remote-stdio bridge, tunnel helpers |
| `scripts/sync_agent_stack.py` | Renders per-harness MCP projections |
| `mcp/mcphub/server.py` | First-party metadata/status tool only |

## Constraints and edge cases

- Secrets belong only in `.env.mcphub` (gitignored); bearer token required for `/mcp`.
- `personal` and `experimental` groups are sensitive; tunnel exposure is opt-in.
- `mcp/servers/` and `mcp/secrets/` are local-only; never ingest into KB.

## Provenance

| Claim or section | Raw or canonical material | Notes |
|------------------|---------------------------|-------|
| Control plane model | `kb/raw/sources/mcphub-control-plane-source.md` | Primary |
| Registry split and safety | `kb/raw/sources/mcp-surfaces.md` | Complementary |

## Related wiki pages

- [[mcp-configuration-and-safety]]
- [[plugin-and-mcp-ownership]]
- [[harness-and-platform-sync]]

## Open questions

- In-tree automated registry-to-mcp_settings generator vs manual regenerate workflow.