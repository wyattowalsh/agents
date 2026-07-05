# Validation Matrix

| Surface | Command | Expected Result | Notes |
|---------|---------|-----------------|-------|
| OpenSpec artifacts | `uv run wagents openspec validate` | Change artifacts validate | After creating and completing tasks. |
| Registry parity | `just mcphub-generate-check` | Settings match registry | Regenerate before check if needed. |
| Settings invariants | `bash scripts/mcphub/validate-settings.sh` | exit 0 | Bearer auth and group membership valid. |
| Repo sync | `uv run python scripts/sync_agent_stack.py --targets repo --apply` | MCP mirrors updated | Do not hand-edit generated surfaces. |
| Registry tests | `uv run pytest tests/test_open_websearch_registry.py -q` | pass | Group contract assertions. |
| Asset validation | `uv run wagents validate` | pass | Includes catalog quarantine checks. |
| Catalog preview | `uv run wagents skills sync --dry-run` | open-websearch row reconciles | No `--apply` unless requested. |
| Docs | `uv run wagents docs generate --no-installed && uv run wagents docs build` | pass | Catalog + MCP registry pages. |
| Package probe | `MODE=stdio SEARCH_MODE=request npx -y open-websearch@latest` | stdio handshake | Inspector optional. |

## Blockers

- None known at proposal time.

## Deferred Checks

- Home sync (`--targets home --apply`)
- Live `wagents skills sync --apply`
- Playwright-enabled Bing path
- Promotion into `daily`, `coding`, or `review` groups