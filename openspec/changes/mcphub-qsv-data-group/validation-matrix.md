# Validation Matrix

| Check | Command |
|-------|---------|
| Registry pytest | `uv run pytest tests/test_qsv_mcp_registry.py -q` |
| MCPHub generate | `just mcphub-generate && just mcphub-generate-check` |
| MCPHub validate | `just mcphub-validate` |
| Asset validate | `uv run wagents validate` |
| Docs generate | `uv run wagents docs generate --no-installed` |
| Skills dry-run | `uv run wagents skills sync --dry-run --strict-pin --format json` |
| OpenSpec | `uv run wagents openspec validate` |
| Stack check | `uv run python scripts/sync_agent_stack.py --targets repo --check` |
