# Validation Matrix

| Surface | Command | Expected Result |
|---------|---------|-----------------|
| Settings parity | `just mcphub-generate-check` | exit 0 |
| MCPHub schema | `just mcphub-validate` | exit 0 |
| Shell wrapper | `shellcheck scripts/mcphub/scrapling-stdio.sh` | exit 0 |
| Registry tests | `uv run pytest tests/test_scrapling_registry.py -q` | pass |
| Repo assets | `uv run wagents validate` | pass |
| OpenSpec | `uv run wagents openspec validate` | pass |
| Repo sync | `uv run python scripts/sync_agent_stack.py --targets repo --check` | no drift |
| Docs | `uv run wagents docs generate --no-installed && uv run wagents docs build` | pass |
| Runtime tools/list (`G-RUNTIME`) | `bash scripts/mcphub/scrapling-stdio.sh` stdio probe (initialize → initialized → tools/list) | bounded registry tools present; see `tools-list.json` |

## Package probe

```bash
uvx --from 'scrapling[ai]==0.4.10' scrapling --version
```

## Deferred Checks

- Home sync (`--targets home --apply`)
- MCPHub endpoint-level `tools/list` at `/mcp/scrapling` (stdio probe is authoritative)
- Promotion into `daily`, `coding`, or `review` groups