# Validation Matrix

| Gate | Command | Expected |
| --- | --- | --- |
| Eval validation | `uv run wagents eval validate --format json` | Passes with no duplicate-prompt errors |
| Eval coverage | `uv run wagents eval coverage --format json` | All skills still report eval coverage |
| CLI tests | `uv run pytest tests/test_eval_cli.py -q` | Duplicate prompt regression passes |
| Audit tests | `uv run pytest tests/test_skill_creator_audit.py -q` | Audit duplicate prompt finding passes |
| Toolkit copies | `uv run pytest tests/test_skill_bundled_toolkit.py -q` | Bundled toolkit modules remain present; eligible `validate_evals.py` copies match the canonical `skill-creator` source, excluding `skills/research/scripts/asset_toolkit/validate_evals.py` while the research guard is active |
| OpenSpec | `npx -y @fission-ai/openspec@latest validate enforce-unique-eval-prompts --type change --json --strict` | Scoped change passes; full OpenSpec validation may still be blocked by unrelated active changes |
| Docs | `uv run wagents docs generate --no-installed --check` | Generated docs up to date |
| Repo validation | `uv run wagents validate --format json` | Passes |
