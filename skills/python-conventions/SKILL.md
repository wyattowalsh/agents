---
name: python-conventions
description: >-
  Python tooling conventions. Use uv for all operations (uv run, uv add — not pip).
  Use pyproject.toml with uv add (not uv pip). Use ty for type checking (not mypy).
  Preferred libraries: loguru, tenacity, tqdm, fastapi, typer, alembic, sqlmodel, gradio, numpy.
user-invocable: false
license: MIT
metadata:
  author: wyattowalsh
  version: "1.0.0"
---

# Python Conventions

Apply these conventions when working on Python files or projects.

## Tooling

- **Package manager**: `uv` for all Python operations (`uv run python ...` instead of `python`, `uv add` instead of `pip install`)
- **Project config**: `pyproject.toml` with `uv add <pkg>` (never `uv pip install` or `pip install`)
- **Type checking**: `ty` (not mypy)

## Preferred Libraries

When applicable, prefer these libraries over alternatives:

| Purpose | Library |
|---------|---------|
| Logging | `loguru` |
| Retries | `tenacity` |
| Progress bars | `tqdm` |
| Web APIs | `fastapi` |
| CLI tools | `typer` |
| DB migrations | `alembic` |
| DB ORM | `sqlmodel` |
| UI/demos | `gradio` |
| Numerics | `numpy` |
