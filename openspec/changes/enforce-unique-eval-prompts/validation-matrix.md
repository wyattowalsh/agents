# Validation Matrix

| Gate | Command | Expected |
| --- | --- | --- |
| Eval validation | `uv run wagents eval validate --format json` | Passes with no duplicate-prompt errors |
| Eval coverage | `uv run wagents eval coverage --format json` | All skills still report eval coverage |
| CLI tests | `uv run pytest tests/test_eval_cli.py -q` | Duplicate prompt regression passes |
| Audit tests | `uv run pytest tests/test_skill_creator_audit.py -q` | Audit duplicate prompt finding passes |
| Toolkit copies | `uv run pytest tests/test_skill_bundled_toolkit.py -q` | Bundled toolkit modules remain present |
| OpenSpec | `uv run wagents openspec validate --format json` | Passes |
| Docs | `uv run wagents docs generate --no-installed --check` | Generated docs up to date |
| Repo validation | `uv run wagents validate --format json` | Passes |
