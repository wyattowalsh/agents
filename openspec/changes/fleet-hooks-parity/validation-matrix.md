# Validation Matrix

| Check | Command | Expectation |
|-------|---------|-------------|
| Shared renderer + sync hooks | `uv run pytest tests/test_sync_agent_stack.py -q` | green |
| APM materialize hooks | `uv run pytest tests/test_apm_materialize.py -q` | green |
| Schema conformance | `uv run pytest tests/test_distribution_metadata.py -q` | green |
| Lint changed Python | `uv run ruff check wagents/hooks scripts/sync_agent_stack.py wagents/apm.py wagents/platforms/base.py` | no errors |
| Asset validation | `uv run wagents validate` | passes |
| OpenSpec validation | `uv run wagents openspec validate` | passes |

## Notes

- No `sync --apply --targets home` is run in this gate.
- Hook output for every harness is unchanged; tests assert shape stability.
