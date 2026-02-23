# Python Convention Exceptions

When to break the standard Python conventions in this repo.

## When pip Is Acceptable

- Legacy project with `requirements.txt` and no migration planned
- Corporate environment that mandates pip with a private index
- Docker images that use pip for minimal layer size (document the reason)

## When mypy Is Acceptable

- Project already has extensive mypy configuration and type stubs
- CI pipeline uses mypy with strict mode and custom plugins
- Migration to ty would require rewriting type stubs (defer to a dedicated PR)

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
