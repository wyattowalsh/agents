## Validation Matrix

| Gate | Command | Result | Notes |
|------|---------|--------|-------|
| Ruff lint | `uv run ruff check` | Pass | Includes `skills/**/scripts/**/*.py` (Wave 6) |
| Ruff format | `uv run ruff format --check` | Pass | 314 files formatted |
| ty | `uv run ty check` | Pass | Scoped to `wagents`, `scripts`, `tests`, `skills/nerdbot` |
| Tooling parity | `uv run pytest tests/test_python_tooling_config.py -q` | Pass (6) | Includes skills scripts include assertion |
| Doctor integration | `uv run pytest tests/test_cli_integration.py::test_doctor_json_success -q` | Pass | |
| Assets | `uv run wagents validate` | Pass | |
| Package dry-run | `uv run wagents package --all --dry-run` | Pass | Research hooks registry-projected |
| Catalog index | `uv run wagents catalog index --check` | Pass | shadcn install-now authoring row |
| OpenSpec | `uv run wagents openspec validate` | Pass (55/55) | Wave 6 delta in ci-evals-observability |
| Full pytest | `uv run pytest -q` | Pass (916) | 2026-06-23 |
| Pre-commit | `pre-commit run ruff ruff-format ty --all-files` | Pass | Config-driven local hooks |