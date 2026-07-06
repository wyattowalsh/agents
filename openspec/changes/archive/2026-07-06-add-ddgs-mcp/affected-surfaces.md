# Affected Surfaces

## Source Of Truth

- `config/mcp-registry.json`
- `openspec/changes/add-ddgs-mcp/*`
- `openspec/changes/add-ddgs-mcp/audit/ddgs-provenance.md`
- `skills/mcphub-operator/SKILL.md`
- `skills/research/references/source-selection.md`

## Generated Outputs

- `mcp/mcphub/mcp_settings.json`
- `mcp.json`
- `.vscode/mcp.json`
- `opencode.json` (via sync)
- `config/codex-config.toml` (via sync)

## Downstream Agent Artifacts

- Repo MCP surfaces updated by `uv run python scripts/sync_agent_stack.py --targets repo --apply`
- Harness parity guard in `scripts/validate/collectors/mcphub_settings.py`
- Optional home/global surfaces via `--targets home --apply` (maintainer opt-in)

## Tests

- `tests/test_ddgs_registry.py`
- `tests/test_sync_agent_stack.py` (harness/daily group parity)
- `tests/test_generate_mcphub_settings.py`, `tests/test_mcphub_settings_collector.py`

## Validation Commands

- `just mcphub-generate` and `just mcphub-generate-check`
- `bash scripts/mcphub/validate-settings.sh`
- `uv run python scripts/sync_agent_stack.py --targets repo --check`
- `uv run wagents validate`
- `uv run wagents openspec validate`
- `uv run pytest tests/test_ddgs_registry.py`
- `uv run wagents docs compose --regen-configs --config mcp-registry`