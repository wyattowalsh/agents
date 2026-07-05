# Proposal

## Problem

The managed MCP registry exposes `duckduckgo-search` for privacy-focused web search but not `ddgs-mcp-server`, which adds metasearch (`search_text`), news (`search_news`), and optional full-page extraction. Research and harness workflows cannot use that surface consistently through MCPHub.

## Intent

Register `ddgs` once in `config/mcp-registry.json`, add it alongside `duckduckgo-search` in applicable MCPHub groups (including `harness`), regenerate tracked settings and repo harness projections, and refresh docs.

## Scope

- Add `ddgs` as an enabled stdio MCP server launched with `uvx ddgs-mcp-server` (PyPI 0.5.1, `auth_policy: none`).
- Insert `ddgs` after `duckduckgo-search` in groups: `harness`, `daily`, `coding`, `research`, `review`, `web-search`, `shared-read`.
- Regenerate `mcp/mcphub/mcp_settings.json` and repo MCP surfaces via sync.
- Update harness parity guards, docs, mcphub-operator skill, and research source-selection references.

## Out Of Scope

- First-party code under `mcp/ddgs/`.
- Replacing or removing `duckduckgo-search`.
- Adding `ddgs` to `tunnel`, `credentialed`, or `experimental` groups.
- Home/global sync unless maintainer explicitly requests `--targets home`.

## Risks

- Upstream `ddgs-mcp-server` is newer and smaller than `duckduckgo-mcp-server`; scraping may hit rate limits.
- `search_text` with `fetch_full_content: true` can return very large tool payloads and add latency.
- `harness` schema grows by one server and two tools.

## Affected Surfaces

- `config/mcp-registry.json`, `mcp/mcphub/mcp_settings.json`
- `mcp.json`, `.vscode/mcp.json`, `opencode.json` (via sync)
- Docs: `docs/ai-tools/mcphub.md`, harness-config/mcp-registry.mdx, mcp/index.mdx
- Skills: mcphub-operator, research references