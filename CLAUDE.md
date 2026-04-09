@AGENTS.md
@/Users/ww/dev/projects/agents/instructions/global.md

## Claude Code

- Use `uv` for all Python operations (`uv run`, `uv add`, not `pip`).
- Prefer: loguru, tenacity, tqdm, fastapi, typer, sqlmodel, fastmcp.
- Run `uv run wagents validate` before committing changes.
- Run `uv run pytest` before committing changes.
- Run `uv run ruff check wagents/` to lint.
- Run `uv run --with ty==0.0.29 ty check` to type-check `wagents/` and `scripts/`.
