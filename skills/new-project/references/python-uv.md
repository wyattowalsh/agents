# Python And uv

Use `uv` for Python project operations and `uvx` for one-off tools before a project environment exists.

## Defaults

- New project: `uv init`
- Runtime dependency: `uv add <package>`
- Development dependency: `uv add --group dev <package>`
- Run command: `uv run <command>`
- One-off tool: `uvx <tool>`
- Validate tests: `uv run pytest`

Keep Python configuration in `pyproject.toml`. Use uv workspaces only for multi-package projects.

## Library Preferences

Use FastAPI for APIs, Typer for CLIs, Textual for TUIs, HTTPX for HTTP, Pydantic v2 and Pydantic Settings for validation/config, pytest for tests, SQLAlchemy/Alembic for larger database workflows, SQLModel for small typed app models, Polars/DuckDB for fast local analytics, and pandas/PySpark when ecosystem or distributed requirements justify them.
