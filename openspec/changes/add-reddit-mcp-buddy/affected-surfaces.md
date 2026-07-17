# Affected Surfaces

## Source Of Truth

- `config/mcp-registry.json`
- `scripts/mcphub/reddit-mcp-buddy-stdio.sh`
- `openspec/changes/add-reddit-mcp-buddy/*`
- `.env.mcphub.example`
- `docs/ai-tools/mcphub.md`
- `skills/mcphub-operator/references/group-picker.md`
- `skills/mcphub-operator/SKILL.md`
- `docs/src/authoring/skills/mcphub-operator.mdx`
- `docs/src/content/docs/mcp/index.mdx`
- `docs/src/content/docs/surfaces/tools.mdx`
- `kb/raw/sources/mcp-surfaces.md`
- `kb/wiki/topics/mcp-configuration-and-safety.md`
- `kb/wiki/topics/mcphub-control-plane.md`

## Generated Outputs

- `mcp/mcphub/mcp_settings.json`
- `mcp.json`
- `.vscode/mcp.json`
- `opencode.json`
- `config/codex-config.toml`
- `.grok/config.toml` (when repo sync projects it)
- generated docs under `docs/src/content/docs/` when `uv run wagents docs generate` runs

## Downstream Agent Artifacts

- Repo MCP surfaces updated by `uv run python scripts/sync_agent_stack.py --targets repo --apply`
- Optional home/global surfaces via `--targets home --apply` (maintainer opt-in)

## Tests

- `tests/test_reddit_mcp_buddy_registry.py`
- existing `tests/test_generate_mcphub_settings.py`, `tests/test_sync_agent_stack.py`

## Validation Commands

- `just mcphub-generate` and `just mcphub-generate-check`
- `bash scripts/mcphub/validate-settings.sh`
- `uv run python scripts/sync_agent_stack.py --targets repo --check`
- `uv run wagents validate`
- `uv run wagents openspec validate`
- `uv run pytest tests/test_reddit_mcp_buddy_registry.py`
- `uv run wagents docs generate --no-installed` and `uv run wagents docs build`
