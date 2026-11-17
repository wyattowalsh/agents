| Check | Command | Expected |
| --- | --- | --- |
| Preflight contract | `uv run pytest tests/test_grok_delegate_preflight.py -q` | pass |
| Auth unit tests | `uv run pytest tests/test_grok_delegate_auth.py -q` | pass |
| No wagents guard | `uv run pytest tests/test_grok_delegate_no_wagents.py -q` | pass |
| Skill assets | `uv run pytest tests/test_grok_delegate_skill.py -q` | pass |
| Skill check | `uv run python skills/grok-delegate/scripts/check.py` | exit 0 |
| Skill audit | `uv run python skills/skill-creator/scripts/audit.py skills/grok-delegate` | score ≥ 80 |
| Repo validate | `uv run wagents validate` | exit 0 |
| OpenSpec | `uv run wagents openspec validate` | exit 0 |
| Package | `uv run python skills/skill-creator/scripts/package.py skills/grok-delegate --dry-run` | exit 0 |