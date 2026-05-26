---
title: MCP Surfaces
tags:
  - kb
  - source
  - mcp
aliases:
  - MCP source map
kind: source-summary
status: active
updated: 2026-05-07
source_count: 3
---

# MCP Surfaces

## Source Record

| Field | Value |
|-------|-------|
| source_id | `mcp-surfaces` |
| original_location | `AGENTS.md`; `mcp/README.md`; `mcp/.gitignore`; `mcp.json`; `config/mcp-registry.json`; `config/schemas/mcp-registry.schema.json`; `https://github.com/damonxue/mcp-ossinsight`; `https://github.com/soycanopa/SupaThings-MCP`; `https://modelcontextprotocol.io/specification/latest`; `https://opencode.ai/docs/mcp-servers/`; Anthropic MCP docs listed in `https://docs.anthropic.com/llms.txt` |
| raw_path | `kb/raw/sources/mcp-surfaces.md` |
| capture_method | repo-local and external pointer summary |
| captured_at | 2026-05-01 |
| size_bytes | pointer summary only |
| checksum | not captured |
| license_or_access_notes | repo-local canonical material plus official MCP/OpenCode/Anthropic docs; external content is untrusted evidence |
| intended_wiki_coverage | [[mcp-configuration-and-safety]], [[plugin-and-mcp-ownership]], [[harness-and-platform-sync]] |

## Summary

The repository has three MCP concepts that should not be collapsed. `config/mcp-registry.json` is the normalized registry source for projected server config. Root `mcp.json` is a distribution or harness-facing manifest. The `mcp/` directory is a local working area whose `servers`, `cache`, `notes`, and `secrets` areas are machine-local and gitignored. Future first-party MCP servers should follow `mcp/<name>/server.py`, `fastmcp.json`, and `pyproject.toml` conventions.

The official MCP spec describes MCP as an open JSON-RPC based protocol connecting hosts, clients, and servers, with server features such as resources, prompts, and tools. Its security section emphasizes explicit user consent, data privacy, tool safety, and approval for LLM sampling. OpenCode MCP docs add local/remote server config, OAuth behavior, tool disabling, and context-size caveats.

`ossinsight` is tracked as an npx-launched stdio MCP using `npx -y ossinsight-mcp`. The user-requested upstream repo `damonxue/mcp-ossinsight` documents OSSInsight API usage with a public rate limit of 600 requests per hour per IP and no required local credentials, but its README's scoped npm package name was not published when checked on 2026-05-07. The canonical registry therefore uses the published `ossinsight-mcp` package.

`supathings` is tracked as an npx-launched stdio MCP from `soycanopa/SupaThings-MCP` using `npx -y supathings-mcp`. Upstream documentation describes a macOS + Things 3 + Node.js 22+ local integration that can read Things data and create or update Things tasks through local automation capabilities.

## Provenance

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| MCP servers expose tools/resources/prompts to clients over a standardized protocol. | `https://modelcontextprotocol.io/specification/latest` | external official spec | Verified 2026-05-01 by web fetch. |
| MCP tool descriptions and operations require trust and consent controls. | `https://modelcontextprotocol.io/specification/latest` | external official spec | Security section. |
| OpenCode supports local and remote MCP servers and OAuth for remote servers. | `https://opencode.ai/docs/mcp-servers/` | external official docs | Verified 2026-05-01 by web fetch. |
| Repo MCP source surfaces are split across registry, generated manifest, and local workspace. | `AGENTS.md`; `mcp/README.md`; `config/mcp-registry.json`; `mcp.json` | canonical material | Do not ingest `mcp/secrets/`. |
| OSSInsight MCP launches with `npx -y ossinsight-mcp` and uses the OSSInsight public API. | `https://github.com/damonxue/mcp-ossinsight`; npm registry metadata for `ossinsight-mcp` | external upstream README and package registry | Verified 2026-05-07. The upstream README scoped package returned npm 404, while `ossinsight-mcp` resolved and exposes a matching MCP package. Public API limit noted as 600 requests/hour/IP. |
| SupaThings MCP launches with `npx -y supathings-mcp` and integrates with local Things 3 on macOS. | `https://github.com/soycanopa/SupaThings-MCP` | external upstream README | Verified 2026-05-07 by web fetch. Requires Things 3 and Node.js 22+ for full runtime behavior. |
