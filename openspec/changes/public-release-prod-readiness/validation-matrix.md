## Validation Matrix

- `uv run pytest -q`
- `uv run ruff check wagents/ tests/ scripts/validate/ skills/skill-creator/scripts/`
- `uv run ruff format --check wagents/ tests/ scripts/validate/ skills/skill-creator/scripts/`
- `uv run ty check --output-format github --no-progress`
- `uv run wagents validate`
- `uv run wagents readme --check`
- `uv run wagents openspec validate`
- `uv run wagents catalog index --check`
- `uv run wagents skills sync --dry-run`
- `uv run python skills/skill-creator/scripts/audit.py --all --strict`
- `uv build`
- built-wheel smoke test in an isolated environment
- `uv run wagents package --all --dry-run`
- `uv run wagents docs generate --no-installed`
- `pnpm --dir docs install --frozen-lockfile`
- `pnpm --dir docs exec astro check`
- `pnpm --dir docs build`
- public-surface local path and secret scan

Exit requires two consecutive full clean runs after post-validation cleanup.
