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
updated: 2026-06-25
source_count: 6
---

# MCP Configuration And Safety

## Scope

This page maps MCP surfaces and safety constraints for repo operation. It does not list secret values or endorse every configured server.

## Summary

MCP in this repo spans three layers: normalized registry, projected manifest, and local workspace. `config/mcp-registry.json` is the normalized registry, root `mcp.json` is a harness/distribution manifest, and `mcp/` is a local workspace with ignored machine-local areas. Do not ingest `mcp/secrets/` or credential-bearing config into the KB.

The official MCP spec defines hosts, clients, and servers communicating through JSON-RPC. Servers can expose resources, prompts, and tools; clients can expose features such as roots, sampling, and elicitation. MCP safety depends on consent, data privacy, and tool safety because tools can represent arbitrary code execution. Tool descriptions and annotations should be treated as untrusted unless they come from a trusted server.

OpenCode docs add repo-relevant details: OpenCode supports local and remote MCP servers, remote OAuth, tool disabling, per-agent enablement, and context-size caveats. In this repo, plugin/MCP ownership rules decide which harness owns Chrome DevTools and other shared servers.

Two registry-managed npx MCPs require specific safety framing. `ossinsight` calls the upstream OSSInsight public API and may be constrained by public IP-based rate limits. `supathings` is local to macOS Things 3 and can read local task data and create or update Things items, so it should be treated as a local personal-data and write-capable MCP even though it does not require committed secrets.

## MCPHub operational safety (Wave 07)

When `mcphub.enabled` is true, local MCP safety adds a fourth concern beyond registry/manifest/workspace: **running process and exposure policy** managed by `scripts/mcphub/`.

| Surface | Safety rule |
|---------|-------------|
| Tracked settings | `mcp/mcphub/mcp_settings.json` must stay secret-free; `make mcphub-validate` enforces registry parity and bearer-routing invariants |
| Live secrets | `.env.mcphub` only — bearer token, tunnel token, API keys, `DB_URL` for smart routing |
| Loopback bind | MCPHub serves on `127.0.0.1:46683`; doctor notes OpenAPI is public path but host should remain local |
| Bearer auth | Required for `/mcp`; `enableBearerAuth` must stay true; smoke test fails without real token |
| Managed processes | Stop helpers refuse to kill PIDs that are not repo-managed `npx @samanhappy/mcphub` / LaunchAgent children |
| Public tunnel | Opt-in (`MCPHUB_TUNNEL_ENABLED`); remote ChatGPT/harness exposure should use bounded `harness-safe` URL only |
| Sensitive groups | `personal` (Gmail, LinkedIn) and `experimental` must not be default tunnel or harness projections |
| Smart routing | Off by default; enabling adds DB + embedding dependencies and `/mcp/$smart` surface |
| Chrome DevTools | Local Chrome profile + debug port 9333; browser automation is high-trust |
| Docling | Runs in isolated `.mcphub/docling-workdir` via `uvx`; local document processing |

Stdio-only harnesses reach MCPHub through `remote-stdio.sh` (`mcp-remote` with bearer header). Treat the bridge token like any other MCP credential — env-only, never tracked in JSON.

## Evidence

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| Repo MCP state is split across registry, manifest, and local workspace. | `kb/raw/sources/mcp-surfaces.md` | raw source note | Prevents conflating source surfaces. |
| MCP defines hosts, clients, servers, tools, resources, and prompts. | `kb/raw/sources/mcp-surfaces.md` | external source note | Official MCP spec. |
| MCP safety requires consent and care around arbitrary tool execution. | `kb/raw/sources/mcp-surfaces.md` | external source note | Official MCP security section. |
| OpenCode supports local and remote MCP config. | `kb/raw/sources/mcp-surfaces.md`; `kb/raw/sources/external-harness-docs.md` | external source notes | Verified OpenCode docs. |
| OSSInsight and SupaThings are registry-managed npx MCPs with different safety profiles. | `kb/raw/sources/mcp-surfaces.md`; `config/mcp-registry.json` | raw source note and canonical config | OSSInsight is public API/rate-limit sensitive; SupaThings is local Things 3 data/write sensitive. |
| MCPHub settings validation enforces no tracked secrets and routing/auth invariants. | `kb/raw/captures/mcphub-settings-validation-capture-w07.md`; `scripts/mcphub/validate_settings.py` | raw capture and canonical script | `make mcphub-validate` returned `ok` on 2026-06-25. |
| Tunnel and LaunchAgent credentials stay env-only; public surface is harness-safe bounded. | `kb/raw/captures/mcphub-launch-tunnel-capture-w07.md`; `mcp/mcphub/README.md` | raw capture and canonical README | Zapier webhook optional; Cloudflare token not committed. |
| Managed PID stop guards and stale-process recovery. | `kb/raw/captures/mcphub-scripts-lifecycle-capture-w07.md`; `scripts/mcphub/common.sh` | raw capture and canonical script | Prevents killing unrelated listeners. |

## Related

- [[mcphub-control-plane]]
- [[plugin-and-mcp-ownership]]
- [[harness-and-platform-sync]]
- [[known-risks-and-open-gaps]]
