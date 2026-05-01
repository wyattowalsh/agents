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
updated: 2026-05-01
source_count: 4
---

# Plugin And MCP Ownership

## Scope

This page maps ownership rules for plugin and MCP surfaces. It avoids user-local secrets and profile paths.

## Summary

Plugin and MCP ownership prevents duplicate tools, conflicting launches, and harness drift. Repo registries model Chrome DevTools and other MCP owners across harnesses. OpenCode remains a repo-MCP owner for Chrome DevTools in this machine's policy, but user-local overrides may replace the generic launch shape without changing the shared repo default.

OpenCode plugins extend runtime behavior through local files or npm packages. Official docs state npm plugins install automatically with Bun and local plugins load from plugin directories. In this repo, runtime plugins belong in `opencode.json`; TUI-only plugins belong in user TUI config unless a tracked TUI config source is introduced.

## Evidence

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| MCP/plugin registries model one-owner rules. | `kb/raw/sources/config-registries-and-sync.md`; `kb/raw/sources/mcp-surfaces.md` | raw source notes | Avoid duplicate server ownership. |
| OpenCode plugins can be local files or npm packages. | `kb/raw/sources/opencode-policy-and-runtime-plugins.md`; `kb/raw/sources/external-harness-docs.md` | external source notes | Official OpenCode docs. |
| Runtime plugins are repo-managed in `opencode.json`; TUI-only plugins are user-owned. | `kb/raw/sources/opencode-policy-and-runtime-plugins.md` | raw source note | Repo policy. |

## Related

- [[mcp-configuration-and-safety]]
- [[opencode-runtime-policy]]
- [[harness-and-platform-sync]]
