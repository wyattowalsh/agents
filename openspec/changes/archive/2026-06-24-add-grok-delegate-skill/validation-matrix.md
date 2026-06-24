| Check | Command | Expected |
| --- | --- | --- |
| Skill audit | `uv run python skills/skill-creator/scripts/audit.py grok-delegate` | score ≥ 80 |
| Skill check | `uv run python skills/grok-delegate/scripts/check.py` | exit 0 |
| Validate | `uv run wagents validate` | exit 0 |
| Grok doctor JSON | `uv run wagents grok doctor --format json` | valid JSON, `ok` boolean |
| Sync codex | `uv run wagents skills sync --dry-run -a codex` | includes grok-delegate |
| Sync opencode | `uv run wagents skills sync --dry-run -a opencode` | includes grok-delegate |
| Sync grok | `uv run wagents skills sync --dry-run -a grok` | includes grok-delegate |
| Pytest | `uv run pytest tests/test_grok_doctor_json.py tests/test_cli_integration.py::TestGrokDoctor -q` | pass |
| Docs build | `uv run wagents docs build` | pass links |