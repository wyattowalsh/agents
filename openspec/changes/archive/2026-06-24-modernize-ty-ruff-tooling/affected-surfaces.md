## Affected Surfaces

- `pyproject.toml` — Ruff/ty SSOT, version pins, include/exclude, overrides
- `uv.lock` — ty/ruff resolved versions
- `Makefile` — lint, format, typecheck, check-python targets
- `.github/workflows/ci.yml`, `.github/workflows/release-skills.yml`
- `.pre-commit-config.yaml`
- `CLAUDE.md`, `GEMINI.md`
- `.claude/rules/python-quality.md`, `.github/instructions/python-quality.instructions.md`
- `skills/python-conventions/references/tooling-contract.md`
- `wagents/cli.py` — doctor ruff/ty checks
- `hooks/lint-check.sh`, `hooks/verify-before-stop.sh`, `hooks/teammate-idle-gate.sh`
- `skills/nerdbot/pyproject.toml`
- `tests/test_python_tooling_config.py`
- Gated Python sources under wagents/, tests/, scripts/, skills/skill-creator/scripts/, skills/nerdbot/