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
updated: 2026-06-25
source_count: 3
---

# MCPHub Control Plane

## Summary

MCPHub is the preferred local MCP control plane when enabled in `config/mcp-registry.json`. Edit servers once in the registry, keep `mcp/mcphub/mcp_settings.json` secret-free and validated, and let clients connect to MCPHub on `http://127.0.0.1:46683` via group or server endpoints instead of launching duplicate standalone processes.

## Why it matters

- Reduces per-harness MCP process sprawl and centralizes auth, routing, and groups.
- `harness-safe` is the primary shared group for managed harness surfaces (14 servers in that group).
- One-owner-per-harness rules still apply (especially Chrome DevTools).
- Contributor defaults enforce deny-by-default tool policy with no wildcard opt-in unless explicit.

## Current shape (2026-06-25)

| Component | Role |
|-----------|------|
| `config/mcp-registry.json` | Canonical SSOT: 33 servers, 11 groups, 6 client projections |
| `mcp/mcphub/mcp_settings.json` | Tracked derived settings (placeholders only) |
| `scripts/mcphub/` | Launch, doctor, validate, remote-stdio bridge, tunnel helpers |
| `scripts/sync_agent_stack.py` | Renders per-harness MCP projections |
| `mcp/mcphub/server.py` | First-party metadata/status tool only |

## Groups and client exposure

| Group | Purpose |
|-------|---------|
| `harness-safe` | Default shared bundle for search, docs, browser, package metadata, fetch, Gmail |
| `all-managed` | Full enabled server set |
| `research` / `reasoning` | Retrieval and structured-thinking bundles |
| `personal` | Gmail, LinkedIn — sensitive |
| `experimental` | Less-proven servers behind explicit targeting |

| Client | Exposure pattern |
|--------|------------------|
| `default`, `codex`, `grok`, `chatgpt` | `harness-safe` group only |
| `opencode` | All 11 groups plus per-server endpoints |
| `stdio_bridge` | stdio bridge for claude-desktop, cursor, gemini-cli, antigravity, github-copilot-cli, crush, chatgpt |

Projection adapters: `codex` → `remote-stdio`; `grok` and `opencode` → `http`. Public tunnel URL `https://mcp.w4w.dev/mcp` when exposed; bearer via `MCPHUB_BEARER_TOKEN`.

## Constraints and edge cases

- Secrets belong only in `.env.mcphub` (gitignored); bearer token required for `/mcp`.
- `personal` and `experimental` groups are sensitive; tunnel exposure is opt-in.
- Smart routing (`/mcp/$smart`) is env-gated and off by default.
- `mcp/servers/` and `mcp/secrets/` are local-only; never ingest into KB.

## Evidence

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| 33 servers, 11 groups, MCPHub enabled | `kb/raw/captures/mcp-registry-capture-w03.md` | raw capture | 2026-06-25 registry read |
| `harness-safe` default client group | `kb/raw/captures/mcp-registry-capture-w03.md` | raw capture | 6 client projections |
| Chrome DevTools ownership split | `kb/raw/captures/mcp-registry-capture-w03.md` | raw capture | plugin/extension/repo_mcp lanes |
| Control plane model and settings parity | `kb/raw/sources/mcphub-control-plane-source.md` | raw source note | Primary pointer summary |
| Registry split and safety | `kb/raw/sources/mcp-surfaces.md` | raw source note | Complementary |

## Related wiki pages

- [[mcp-configuration-and-safety]]
- [[plugin-and-mcp-ownership]]
- [[harness-and-platform-sync]]
- [[sync-transaction-safety]]

## Open questions

- In-tree automated registry-to-mcp_settings generator vs manual regenerate workflow.