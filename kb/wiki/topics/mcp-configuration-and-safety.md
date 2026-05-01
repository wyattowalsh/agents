---
title: MCP Configuration And Safety
tags:
  - kb
  - mcp
  - safety
aliases:
  - MCP safety
kind: concept
status: active
updated: 2026-05-01
source_count: 2
---

# MCP Configuration And Safety

## Scope

This page maps MCP surfaces and safety constraints for repo operation. It does not list secret values or endorse every configured server.

## Summary

MCP in this repo spans three layers: normalized registry, projected manifest, and local workspace. `config/mcp-registry.json` is the normalized registry, root `mcp.json` is a harness/distribution manifest, and `mcp/` is a local workspace with ignored machine-local areas. Do not ingest `mcp/secrets/` or credential-bearing config into the KB.

The official MCP spec defines hosts, clients, and servers communicating through JSON-RPC. Servers can expose resources, prompts, and tools; clients can expose features such as roots, sampling, and elicitation. MCP safety depends on consent, data privacy, and tool safety because tools can represent arbitrary code execution. Tool descriptions and annotations should be treated as untrusted unless they come from a trusted server.

OpenCode docs add repo-relevant details: OpenCode supports local and remote MCP servers, remote OAuth, tool disabling, per-agent enablement, and context-size caveats. In this repo, plugin/MCP ownership rules decide which harness owns Chrome DevTools and other shared servers.

## Evidence

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| Repo MCP state is split across registry, manifest, and local workspace. | `kb/raw/sources/mcp-surfaces.md` | raw source note | Prevents conflating source surfaces. |
| MCP defines hosts, clients, servers, tools, resources, and prompts. | `kb/raw/sources/mcp-surfaces.md` | external source note | Official MCP spec. |
| MCP safety requires consent and care around arbitrary tool execution. | `kb/raw/sources/mcp-surfaces.md` | external source note | Official MCP security section. |
| OpenCode supports local and remote MCP config. | `kb/raw/sources/mcp-surfaces.md`; `kb/raw/sources/external-harness-docs.md` | external source notes | Verified OpenCode docs. |

## Related

- [[plugin-and-mcp-ownership]]
- [[harness-and-platform-sync]]
- [[known-risks-and-open-gaps]]
