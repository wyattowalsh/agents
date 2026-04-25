# Python Convention Exceptions

When to break the standard Python conventions in this repo.

## When pip Is Acceptable

- Legacy project with `requirements.txt` and no migration planned
- Corporate environment that mandates pip with a private index
- Docker images that use pip for minimal layer size (document the reason)
- Published package compatibility checks that intentionally compare installer behavior

## Legacy Type Checker Exceptions

- Only keep `mypy` temporarily when migrating an existing codebase to `ty`
- Document the migration owner, scope, and exit criteria
- Prefer isolating legacy `mypy` usage to the package being migrated instead of making it the repo-wide standard
- Keep the target state as `uv run ty check` unless the repo owner explicitly rejects ty for that project

## When Alternative Libraries Are Acceptable

- `flask` over `fastapi` -- existing project with flask middleware and blueprints
- `click` over `typer` -- project needs click's advanced group nesting
- `argparse` over `typer` -- zero-dependency scripts or audit tooling
- `sqlalchemy` over `sqlmodel` -- project uses advanced SQLAlchemy patterns

## Virtual Environment Exceptions

- Conda/mamba environments for data science projects with binary dependencies
- System Python when building OS-level packages (document the constraint)
- Pre-existing `.venv` directories during migration, only until `uv` ownership is established

## Monorepo Exceptions

- Sub-packages that publish to PyPI may need their own isolated `pyproject.toml`
- Use `uv` workspace members when possible; fall back to path dependencies otherwise

## Exception Record Template

Every approved exception should name:

| Field | Required Content |
|-------|------------------|
| Reason | The external or legacy constraint forcing the exception |
| Owner | Person, team, or issue responsible for removing or maintaining it |
| Scope | Exact package, service, command, or file family affected |
| Exit criteria | Observable condition that ends the exception |
| Target state | Default convention to return to, usually `uv`, `uv run ty check`, Ruff, pytest, and `pyproject.toml` |
| Validation command | Command proving the exception still works while it exists |

Do not approve broad exceptions such as "this repo uses pip" when the evidence only applies to one package or container layer.
