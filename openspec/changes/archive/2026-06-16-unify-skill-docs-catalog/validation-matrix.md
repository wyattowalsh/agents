# Validation Matrix

| Check | Command |
|-------|---------|
| Unit tests | `uv run pytest tests/test_docs.py tests/test_skill_docs.py tests/test_skill_research.py tests/test_sync_desired_skills.py` |
| Docs generate | `uv run wagents docs generate --no-installed` |
| Docs build | `cd docs && pnpm build` |
| Sync desired set | `uv run wagents skills sync --dry-run --agent codex` |
| Lint / types | `uv run ruff check wagents/ && uv run ty check wagents/` |
| Research planner | `uv run wagents docs research --dry-run --source-type custom --no-installed` |
| Research gate (optional) | `uv run wagents docs research --check-research --source-type custom --no-installed` |
