# Change: Add Harness Safe MCPHub Group

## Why

Managed harnesses should use a bounded MCPHub surface instead of the full
MCPHub `all` endpoint. The requested surface includes search, browser
inspection, docs, fetching, package metadata, repository packing, Supabase,
Tavily, Trafilatura, DuckDuckGo, and Gmail.

## What Changes

- Add an `harness-safe` MCPHub group to the canonical MCP registry and tracked
  MCPHub settings.
- Project managed harnesses to the enabled `mcphub_group_harness-safe`
  endpoint plus disabled individual MCPHub server endpoints.
- Keep bearer auth placeholder handling and stale MCPHub entry stripping.
- Update docs and tests for the new harness-facing MCPHub endpoint.

## Non-Goals

- Removing existing MCPHub groups.
- Removing the harness-specific transport and auth settings for Codex,
  OpenCode, ChatGPT, stdio bridge, or Cherry Studio.
- Disabling MCPHub bearer auth or Smart Routing defaults.
