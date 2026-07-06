# Validation Matrix

| Surface | Command | Expected Result |
|---------|---------|-----------------|
| Settings parity | `just mcphub-generate-check` | exit 0 |
| MCPHub schema | `just mcphub-validate` | exit 0 |
| Repo assets | `uv run wagents validate` | exit 0 |
| OpenSpec | `uv run wagents openspec validate` | change validates |
| Pytest | `uv run pytest tests/test_ddgs_registry.py tests/test_generate_mcphub_settings.py tests/test_sync_agent_stack.py -q -k ddgs or harness` | pass |
| Repo sync | `uv run python scripts/sync_agent_stack.py --targets repo --check` | no drift |
| Docs regen | `uv run wagents docs compose --regen-configs --config mcp-registry` | embed refreshed |
| Runtime smoke | `just mcphub-smoke` + `/mcp/ddgs` tools/list | pass (2026-07-06: `ddgs-search_text`, `ddgs-search_news`) |
| Docs build | `uv run wagents docs build` | **waived** — `starlight-site-graph` pre-existing blocker |

## Package probe

```bash
uvx ddgs-mcp-server
```

PyPI: `ddgs-mcp-server==0.5.1`, requires `ddgs`, `httpx`, `mcp`, `trafilatura`.