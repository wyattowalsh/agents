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
updated: 2026-05-01
source_count: 1
---

# MCP Surfaces

## Source Record

| Field | Value |
|-------|-------|
| source_id | `mcp-surfaces` |
| original_location | `AGENTS.md`; `mcp/README.md`; `mcp/.gitignore`; `mcp.json`; `config/mcp-registry.json`; `config/schemas/mcp-registry.schema.json`; `https://modelcontextprotocol.io/specification/latest`; `https://opencode.ai/docs/mcp-servers/`; Anthropic MCP docs listed in `https://docs.anthropic.com/llms.txt` |
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

## Provenance

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| MCP servers expose tools/resources/prompts to clients over a standardized protocol. | `https://modelcontextprotocol.io/specification/latest` | external official spec | Verified 2026-05-01 by web fetch. |
| MCP tool descriptions and operations require trust and consent controls. | `https://modelcontextprotocol.io/specification/latest` | external official spec | Security section. |
| OpenCode supports local and remote MCP servers and OAuth for remote servers. | `https://opencode.ai/docs/mcp-servers/` | external official docs | Verified 2026-05-01 by web fetch. |
| Repo MCP source surfaces are split across registry, generated manifest, and local workspace. | `AGENTS.md`; `mcp/README.md`; `config/mcp-registry.json`; `mcp.json` | canonical material | Do not ingest `mcp/secrets/`. |
