# Validation Matrix

| Surface | Command | Expected Result |
|---------|---------|-----------------|
| Settings parity | `just mcphub-generate-check` | exit 0 |
| MCPHub schema | `just mcphub-validate` | exit 0 |
| Repo assets | `uv run wagents validate` | exit 0 |
| OpenSpec | `uv run wagents openspec validate` | change validates |
| Pytest | `uv run pytest tests/test_generate_mcphub_settings.py tests/test_sync_agent_stack.py::test_repo_workflow_groups_and_bounded_clients tests/test_mcphub_endpoints.py -q` | pass |
| Repo sync | `uv run python scripts/sync_agent_stack.py --targets repo --check` | no drift |
| Docs | `uv run wagents docs build` | pass |

## Package probe

```bash
uvx ddgs-mcp-server
```

PyPI: `ddgs-mcp-server==0.5.1`, requires `ddgs`, `httpx`, `mcp`, `trafilatura`.