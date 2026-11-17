# Affected Surfaces

## Source

- `config/mcp-registry.json`
- `scripts/mcphub/mcp_response.py`
- `scripts/mcphub/smoke.sh`
- `tests/test_ddgs_registry.py`
- `tests/test_mcphub_mcp_response.py`

## Generated

- `mcp/mcphub/mcp_settings.json`
- `docs/src/content/docs/harness-config/mcp-registry.mdx`

## Docs

- `docs/ai-tools/mcphub.md`
- `docs/src/content/docs/mcp/index.mdx`

## Runtime

- MCPHub `/mcp`
- MCPHub `/mcp/ddgs`
- MCPHub `/mcp/harness`
- Harnesses consuming MCPHub `harness`, `daily`, `coding`, `research`, `review`, `web-search`, or `shared-read` groups
