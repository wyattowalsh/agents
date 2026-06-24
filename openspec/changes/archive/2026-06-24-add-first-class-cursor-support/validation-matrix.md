# Validation Matrix

| Surface | Command | Expected Result |
| --- | --- | --- |
| Adapter and sync tests | `uv run pytest tests/test_sync_agent_stack.py tests/test_platform_adapters.py -q --tb=short` | Cursor repo rendering and sync delegation pass. |
| Hook tests | `uv run pytest tests/test_wagents_hook.py -q --tb=short` | Cursor native hook output and policy registry coverage pass. |
| Repo validation | `uv run wagents validate` | Cursor schema/config and assets validate. |
| Cursor sync check | `uv run python scripts/sync_agent_stack.py --check --platforms cursor --targets repo` | No Cursor drift after apply. |
| OpenSpec validation | `uv run wagents openspec validate` | Change package and updated spec validate. |
| Skills preview | `uv run wagents skills sync --dry-run -a cursor` | Preview only; no live installs. |
| Docs | `uv run wagents docs generate`, `uv run wagents readme --check`, `uv run wagents docs build` | Docs/readme surfaces are current or failures are reported with exact blocker. |
| Optional Cursor CLI | real Cursor `agent` non-mutating plan/print smoke | Run only if executable identity is confirmed. |
