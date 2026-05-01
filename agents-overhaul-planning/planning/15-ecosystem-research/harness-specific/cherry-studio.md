# Cherry Studio Ecosystem Surface

## Sources

- MCP config: https://docs.cherry-ai.com/docs/en-us/advanced-basic/mcp/config
- MCP environment install: https://docs.cherry-ai.com/docs/en-us/advanced-basic/mcp/install
- Automatic MCP install: https://docs.cherry-ai.com/docs/en-us/advanced-basic/mcp/auto-install
- Built-in MCP: https://docs.cherry-ai.com/docs/en-us/advanced-basic/mcp/buildin

## Extension surfaces

- MCP Server settings UI.
- STDIO command/arguments configuration.
- Built-in uv/bun under `~/.cherrystudio/bin` or Windows equivalent.
- Auto-install beta via `@mcpmarket/mcp-auto-install`.
- Built-in MCP presets such as memory, sequentialthinking, brave-search, fetch, filesystem.

## Planning implications

- Prefer documenting Cherry-specific setup rather than writing repo-local files unless official config export/import is verified.
- Validate that `uvx` install examples are compatible with Cherry's bundled uv behavior.
- Auto-install beta should be marked experimental.
