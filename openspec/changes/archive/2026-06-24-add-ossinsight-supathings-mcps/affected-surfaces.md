# Affected Surfaces

## Source Of Truth

- `config/mcp-registry.json`
- `openspec/changes/add-ossinsight-supathings-mcps/*`
- `kb/raw/sources/mcp-surfaces.md`
- `kb/wiki/topics/mcp-configuration-and-safety.md`

## Generated Outputs

- `mcp.json`
- `.vscode/mcp.json`
- `opencode.json`
- generated docs content under `docs/src/content/docs/` when `uv run wagents docs generate` updates pages
- `README.md` only if generation changes it

## Downstream Agent Artifacts

- Home/global MCP surfaces updated by `uv run python scripts/sync_agent_stack.py --targets home --apply`, including managed Claude Desktop, Cursor, Copilot CLI/shadow, Gemini CLI, Antigravity, OpenCode, ChatGPT, AITK, Crush, Codex, Cherry Studio, and Perplexity Desktop import surfaces where supported.

## Tests

- Existing sync tests in `tests/test_sync_agent_stack.py` cover registry-driven repo sync, generated MCP shape, env placeholder handling, and preservation behavior.

## Validation Commands

- `uv run python scripts/sync_agent_stack.py --targets repo --apply`
- `uv run python scripts/sync_agent_stack.py --targets home --apply`
- `uv run wagents docs generate`
- `uv run python scripts/sync_agent_stack.py --targets repo,home --check`
- `uv run wagents validate`
- `uv run wagents openspec validate`
- targeted package launch probes for `@modelcontextprotocol/server-ossinsight` and `supathings-mcp`
