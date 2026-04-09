# Python Convention Exceptions

When to break the standard Python conventions in this repo.

## When pip Is Acceptable

- Legacy project with `requirements.txt` and no migration planned
- Corporate environment that mandates pip with a private index
- Docker images that use pip for minimal layer size (document the reason)

## Legacy Type Checker Exceptions

- Only keep `mypy` temporarily when migrating an existing codebase to `ty`
- Document the migration owner, scope, and exit criteria
- Prefer isolating legacy `mypy` usage to the package being migrated instead of making it the repo-wide standard

## When Alternative Libraries Are Acceptable

- `flask` over `fastapi` -- existing project with flask middleware and blueprints
- `click` over `typer` -- project needs click's advanced group nesting
- `argparse` over `typer` -- zero-dependency scripts or audit tooling
- `sqlalchemy` over `sqlmodel` -- project uses advanced SQLAlchemy patterns

## Virtual Environment Exceptions

- Conda/mamba environments for data science projects with binary dependencies
- System Python when building OS-level packages (document the constraint)

## Monorepo Exceptions

- Sub-packages that publish to PyPI may need their own isolated `pyproject.toml`
- Use `uv` workspace members when possible; fall back to path dependencies otherwise
