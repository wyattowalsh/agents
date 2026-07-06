# Affected Surfaces

## Source Of Truth

- `config/mcp-registry.json`
- `scripts/mcphub/scrapling-stdio.sh`
- `openspec/changes/add-scrapling-mcp/*`
- `kb/raw/sources/mcp-surfaces.md`
- `kb/wiki/topics/mcp-configuration-and-safety.md`

## Generated Outputs

- `mcp/mcphub/mcp_settings.json`
- `mcp.json`
- `.vscode/mcp.json`
- `opencode.json`
- `config/codex-config.toml`
- generated docs under `docs/src/content/docs/` when `uv run wagents docs generate` runs

## Downstream Agent Artifacts

- Repo MCP surfaces updated by `uv run python scripts/sync_agent_stack.py --targets repo --apply`
- Optional home/global surfaces via `--targets home --apply` (maintainer opt-in)

## Tests

- `tests/test_scrapling_registry.py`
- existing `tests/test_generate_mcphub_settings.py`, `tests/test_sync_agent_stack.py`

## Validation Commands

- `just mcphub-generate` and `just mcphub-generate-check`
- `bash scripts/mcphub/validate-settings.sh`
- `uv run python scripts/sync_agent_stack.py --targets repo --check`
- `uv run wagents validate`
- `uv run wagents openspec validate`
- `uv run pytest tests/test_scrapling_registry.py`
- `uv run wagents docs generate --no-installed` and `uv run wagents docs build`