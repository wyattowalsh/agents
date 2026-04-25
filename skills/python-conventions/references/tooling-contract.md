# Tooling Contract

Use this reference when the task touches Python commands, dependencies, or
completion checks.

## Required Defaults

| Task | Required Command | Reject |
|------|------------------|--------|
| Add runtime dependency | `uv add <pkg>` | `pip install <pkg>`, `uv pip install <pkg>` |
| Add dev dependency | `uv add --group dev <pkg>` | putting test/lint tools in runtime dependencies |
| Remove dependency | `uv remove <pkg>` | manually editing dependency tables without a reason |
| Upgrade one dependency | `uv lock --upgrade-package <pkg>` | ad hoc lockfile edits |
| Reproducible install | `uv sync --locked` | installing from an unlocked or hand-edited lockfile |
| Run Python file/module | `uv run python ...` or `uv run <tool>` | bare `python ...` |
| Type check | `uv run ty check` | `mypy` or bare `ty check` as the default repo recommendation |
| Lint | `uv run ruff check` | ad hoc lint alternatives as repo default |
| Format | `uv run ruff format` | formatter drift without repo approval |
| Test | `uv run pytest` | skipping tests without reason |

## Completion Sequence

1. Install or update runtime dependencies with `uv add <pkg>` when needed.
2. Install development-only tools with `uv add --group dev <pkg>`.
3. Remove dependencies with `uv remove <pkg>`.
4. Upgrade a single locked package with `uv lock --upgrade-package <pkg>`.
5. Use `uv sync --locked` when validating an existing lockfile-backed workflow.
6. Run commands through `uv run`.
7. Run `uv run ruff check`.
8. Run `uv run ruff format` if formatting is part of the task.
9. Run `uv run ty check`.
10. Run `uv run pytest`.

## Workspace and Lockfile Rules

1. Run `uv` commands from the project or workspace root unless a sub-package has its own documented project boundary.
2. Use `uv` workspace members for monorepo sub-packages when possible.
3. Do not edit `uv.lock` by hand. Use `uv add`, `uv remove`, `uv lock`, or `uv sync`.
4. Treat `uv sync --locked` failure as evidence that dependencies or the lockfile are out of sync.
5. Keep dependency metadata in `pyproject.toml`; do not split new dependency state into `requirements.txt` unless `references/exceptions.md` approves an exception.

## Type Checking Nuance

`uv run ty check` is the repo default because `uv run` executes inside the managed project environment where project dependencies, Python version, and `pyproject.toml` configuration are discoverable. Do not replace it with bare `ty check` in repo guidance.

Keep `mypy` only as a temporary migration exception with owner, scope, exit criteria, and target state documented in `references/exceptions.md`.

## Ruff Configuration

1. Configure Ruff in `pyproject.toml` under `[tool.ruff]`, `[tool.ruff.lint]`, and `[tool.ruff.format]` when the project needs explicit settings.
2. Keep lint and format commands separate unless a local script intentionally combines them.
3. Use `uv run ruff check` for lint validation and `uv run ruff format` for formatting.

## Exception Gate

If a request appears to require `pip`, `mypy`, manual virtualenv activation, or
system Python, read `references/exceptions.md` and require a concrete reason,
owner, or migration path before allowing the deviation.
