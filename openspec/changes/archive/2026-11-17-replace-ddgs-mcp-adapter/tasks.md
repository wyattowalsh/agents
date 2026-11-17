# Tasks

- [x] Verify the current adapter exposes only `search_text` and `search_news`.
- [x] Verify upstream `ddgs[mcp]` exposes text, image, news, video, book, and extract tool functions.
- [x] Update `config/mcp-registry.json` to launch upstream DDGS MCP.
- [x] Update DDGS registry tests.
- [x] Regenerate MCPHub settings and registry docs.
- [x] Add hermetic JSON/SSE MCP response parsing and exhaustive fixtures.
- [x] Complete Streamable HTTP lifecycle handling in MCPHub smoke.
- [x] Assert the exact DDGS direct-route tool set and harness-route containment.
- [x] Validate focused registry, response parser, MCPHub settings, docs, shell, and OpenSpec checks.
- [x] Smoke the upstream `ddgs[mcp]` tool list through MCPHub direct and harness routes
  (`just mcphub-doctor && just mcphub-smoke`, 2026-07-12; exact six-tool surface verified).
