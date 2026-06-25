---
title: Plugin And MCP Ownership
tags:
  - kb
  - plugins
  - mcp
aliases:
  - MCP ownership
  - Plugin ownership
kind: concept
status: active
updated: 2026-06-25
source_count: 5
---

# Plugin And MCP Ownership

## Scope

This page maps ownership rules for plugin and MCP surfaces. It avoids user-local secrets and profile paths.

## Summary

Plugin and MCP ownership prevents duplicate tools, conflicting launches, and harness drift. `config/mcp-registry.json` is the canonical server SSOT; per-server `ownership` and `exclude_from_harnesses` fields suppress duplicate projection. Chrome DevTools is the reference case: excluded from claude-code, gemini-cli, github-copilot-web, and vscode; owned via plugin (Claude, Copilot web, VS Code), extension (Gemini), or repo MCP (desktop apps, Codex, OpenCode, Cursor, Grok, and others).

OpenCode remains a repo-MCP owner for Chrome DevTools in this machine's policy, but user-local overrides may replace the generic launch shape without changing the shared repo default.

OpenCode plugins extend runtime behavior through local files or npm packages. Official docs state npm plugins install automatically with Bun and local plugins load from plugin directories. In this repo, runtime plugins belong in `opencode.json`; TUI-only plugins belong in user TUI config unless a tracked TUI config source is introduced.

## MCPHub and ownership

When MCPHub is enabled, clients connect to group endpoints (primarily `harness-safe`) rather than launching standalone copies of managed servers. Ownership rules still govern which harness receives direct MCP config vs plugin/extension delegation — MCPHub does not override one-owner semantics.

| Surface | Owner lane | Example harnesses |
|---------|------------|-------------------|
| `plugin` | Native plugin ships the tool | claude-code, github-copilot-web |
| `extension` | Editor/CLI extension | gemini-cli |
| `repo_mcp` | Repo registry + sync projection | codex, cursor, opencode, grok-build |

Contributor defaults: deny-by-default tools policy; wildcards require explicit opt-in; new servers start with empty tool lists.

## Hook ownership cross-link

`config/hook-surface-registry.json` complements MCP ownership: hooks can be embedded in settings (Claude, Gemini) or standalone JSON (Codex, Cursor). Copilot hooks under `.github/hooks/*` are secondary scaffolding; Grok hooks sync from repo-observed Plannotator policy. See [[harness-and-platform-sync]] for the OpenCode plugin-internal hook blind spot.

## Evidence

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| MCP/plugin registries model one-owner rules. | `kb/raw/sources/config-registries-and-sync.md`; `kb/raw/sources/mcp-surfaces.md` | raw source notes | Avoid duplicate server ownership. |
| Chrome DevTools ownership lanes and exclusions. | `kb/raw/captures/mcp-registry-capture-w03.md` | raw capture | 2026-06-25 registry read. |
| MCPHub `harness-safe` default; stdio bridge clients. | `kb/raw/captures/mcp-registry-capture-w03.md` | raw capture | 33 servers, 6 client projections. |
| Hook discovery paths per harness. | `kb/raw/captures/hook-surface-registry-capture-w03.md` | raw capture | 9 harnesses declared. |
| OpenCode plugins can be local files or npm packages. | `kb/raw/sources/opencode-policy-and-runtime-plugins.md`; `kb/raw/sources/external-harness-docs.md` | external source notes | Official OpenCode docs. |
| Runtime plugins are repo-managed in `opencode.json`; TUI-only plugins are user-owned. | `kb/raw/sources/opencode-policy-and-runtime-plugins.md` | raw source note | Repo policy. |

## Related

- [[mcp-configuration-and-safety]]
- [[mcphub-control-plane]]
- [[opencode-runtime-policy]]
- [[harness-and-platform-sync]]
- [[sync-transaction-safety]]