# Validation Matrix

| Surface | Command | Expected |
|---------|---------|----------|
| Repo discovery | `uv run pytest tests/test_repo_context.py` | Pass |
| CLI integration | `uv run pytest tests/test_cli_integration.py` | Pass |
| Plugins | `uv run pytest tests/test_wagents_plugins.py` | Pass |
| Self commands | `uv run pytest tests/test_wagents_self.py` | Pass |
| Wheel smoke | `uv build && uv tool install dist/wagents-*.whl --force` | `wagents self doctor` exits 0 |
| Repo validate | `wagents validate` from clone | Exit 0 |
| Quality | `uv run ruff check wagents/`; `uv run ty check` | Pass |
| Docs | `uv run wagents docs generate --no-installed`; `uv run wagents docs build` | Pass |