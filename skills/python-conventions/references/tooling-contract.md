# Tooling Contract

Use this reference when the task touches Python commands, dependencies, or
completion checks.

## Required Defaults

| Task | Required Command | Reject |
|------|------------------|--------|
| Add dependency | `uv add <pkg>` | `pip install <pkg>`, `uv pip install <pkg>` |
| Run Python file/module | `uv run python ...` or `uv run <tool>` | bare `python ...` |
| Type check | `uv run ty check` | `mypy` as the default repo recommendation |
| Lint | `uv run ruff check` | ad hoc lint alternatives as repo default |
| Format | `uv run ruff format` | formatter drift without repo approval |
| Test | `uv run pytest` | skipping tests without reason |

## Completion Sequence

1. Install or update dependencies with `uv add` when needed.
2. Run commands through `uv run`.
3. Run `uv run ruff check`.
4. Run `uv run ruff format` if formatting is part of the task.
5. Run `uv run ty check`.
6. Run `uv run pytest`.

## Exception Gate

If a request appears to require `pip`, `mypy`, manual virtualenv activation, or
system Python, read `references/exceptions.md` and require a concrete reason,
owner, or migration path before allowing the deviation.
