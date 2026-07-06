# Validation Matrix

| Surface | Command | Expected Result |
|---------|---------|-----------------|
| Settings parity | `just mcphub-generate-check` | exit 0 |
| MCPHub schema | `just mcphub-validate` | exit 0 |
| Shell wrapper | `shellcheck scripts/mcphub/jupyter-mcp-server-stdio.sh` | exit 0 |
| Registry tests | `uv run pytest tests/test_jupyter_mcp_server_registry.py -q` | pass |
| Repo assets | `uv run wagents validate` | pass |
| OpenSpec | `uv run wagents openspec validate` | pass |
| Repo sync | `uv run python scripts/sync_agent_stack.py --targets repo --check` | no drift |
| Docs | `uv run wagents docs generate --no-installed && uv run wagents docs build` | pass |
| Skill | `uv run python skills/mcphub-operator/scripts/check.py` | pass |

## Package probe

```bash
uvx --from 'jupyter-mcp-server==1.0.2' jupyter-mcp-server --help
```

## Deferred Checks

- Home sync (`--targets home --apply`)
- Runtime `tools/list` on live MCPHub with JupyterLab running (`G-RUNTIME`)
- Promotion into `daily` group