# Validation Matrix

| Surface | Command | Expected |
| --- | --- | --- |
| OpenSpec change | `npx -y @fission-ai/openspec@latest validate add-cursor-plannotator-hooks --strict` | Pass |
| Shim unit tests | `uv run pytest tests/test_plannotator_cursor_plan_hook.py` | CreatePlan deny/allow, SwitchMode plan vs agent, missing binary fail-open, no exit 2, no cross-project plan scan |
| Render / merge | `uv run pytest tests/hooks/test_render_cursor.py tests/hooks/test_merge.py` | SwitchMode/CreatePlan placeholders; stale ExitPlanMode rows replaced; custom rows kept |
| Home sync | `uv run pytest tests/test_cursor_home_sync_pin.py tests/test_sync_agent_stack.py` | Shim copy; `--no-plannotator-hooks` skip; custom MCP/hooks preserved |
| Doctor | `uv run pytest tests/test_cursor_cli_doctor.py` | Warn-only Plannotator checks; `report["ok"]` remains true |
| Python quality | `uv run ruff check` / `uv run ruff format --check` / `uv run ty check` on touched Python | Clean |
| Assets | `uv run wagents validate` | Pass |
| Home apply | `uv run python scripts/sync_agent_stack.py --apply --targets home` or `wagents cursor-cli plannotator sync` | Operator-approved later; not part of this change |

## Known blockers

- Home `~/.cursor/hooks.json` is not updated until an operator applies home sync.
- Enter-context can miss when the user reaches plan mode via `Shift+Tab` / `--plan` without `SwitchMode`.
