# Proposal: Replace DDGS MCP adapter with upstream DDGS MCP

## Problem

The managed `ddgs` MCP registry entry launches the separate `ddgs-mcp-server==0.5.1` adapter. That adapter depends on the `ddgs` library but exposes only `search_text` and `search_news`, so MCPHub correctly lists two tools even though upstream `deedy5/ddgs` now ships a built-in MCP server with text, image, news, video, book, and extraction tools.

## Intent

Replace the adapter launch command with upstream `ddgs[mcp]` via `uvx --from ddgs[mcp] ddgs mcp`, preserving the existing `ddgs` server slug and MCPHub group memberships while expanding the runtime tool surface to upstream DDGS MCP.

## Scope

- Update `config/mcp-registry.json` and generated MCPHub settings.
- Keep `auth_policy: none`, stdio transport, and existing group placement after `duckduckgo-search`.
- Update registry tests and docs to describe the upstream tool surface.
- Validate the complete MCP HTTP lifecycle and both `/mcp/ddgs` and `/mcp/harness` tool-list contracts without exposing credentials or response bodies.
- Preserve the archived `add-ddgs-mcp` change as historical adapter provenance.

## Out Of Scope

- Replacing or removing `duckduckgo-search`.
- Adding `ddgs` to `tunnel`.
- Pinning a specific DDGS version unless a regression requires rollback.
- Running live install/apply workflows outside local MCP launch validation.

## Affected Surfaces

- `config/mcp-registry.json`
- `mcp/mcphub/mcp_settings.json`
- `scripts/mcphub/mcp_response.py` and `scripts/mcphub/smoke.sh`
- `tests/test_ddgs_registry.py`
- `tests/test_mcphub_mcp_response.py`
- Generated MCP registry docs
- `docs/ai-tools/mcphub.md` and MCP overview guidance
