# Validation Matrix

```bash
uv run pytest tests/test_grok_platform.py tests/test_sync_agent_stack.py -q
uv run pytest tests/test_cli_integration.py tests/test_installed_inventory.py -k grok -q
uv run pytest
uv run wagents validate
uv run ruff check wagents/ scripts/sync_agent_stack.py
uv run ty check
uv run python scripts/sync_agent_stack.py --check --targets repo
uv run python scripts/sync_agent_stack.py --apply --platforms grok --targets home
~/.grok/bin/grok inspect
uv run wagents grok doctor
uv run wagents openspec validate
```
