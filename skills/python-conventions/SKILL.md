---
name: python-conventions
description: >-
  Python tooling conventions. Enforce uv, ty. Use when working on .py files
  or pyproject.toml. NOT for JS/TS or shell scripts.
user-invocable: false
disable-model-invocation: false
license: MIT
metadata:
  author: wyattowalsh
  version: "1.0.0"
---

# Python Conventions

Apply these conventions when working on Python files or projects.

## Dispatch

| $ARGUMENTS | Action |
|------------|--------|
| Active (auto-invoked when working on Python files) | Apply all conventions below |
| Empty | Display convention summary |
| `check` | Verify tooling compliance only |

## References

| File | Purpose |
|------|---------|
| `references/exceptions.md` | When to break conventions (legacy, corporate) |
| `references/performance-tips.md` | Profiling tools, optimization patterns quick-reference |
| `references/testing-patterns.md` | Fixture scopes, markers, conftest skeleton |

## Tooling

- **Package manager**: `uv` for all Python operations (`uv run python ...` instead of `python`, `uv add` instead of `pip install`)
- **Project config**: `pyproject.toml` with `uv add <pkg>` (never `uv pip install` or `pip install`)
- **Type checking**: `uv run --with ty==0.0.29 ty check` (not `mypy`)
- **Linting**: `uv run ruff check` and `uv run ruff format`
- **Testing**: `uv run pytest`
- **Task running**: `uv run <command>` for all script execution

### Virtual Environments

- Let `uv` manage virtual environments automatically
- Never manually create or activate `.venv` directories
- Use `uv run` to execute within the project environment

## Preferred Libraries

When applicable, prefer these libraries over alternatives:

| Purpose | Library | Instead of |
|---------|---------|------------|
| Logging | `loguru` | `logging` |
| Retries | `tenacity` | manual retry loops |
| Progress bars | `tqdm` | print statements |
| Web APIs | `fastapi` | flask |
| CLI tools | `typer` | argparse, click |
| DB migrations | `alembic` | manual SQL |
| DB ORM | `sqlmodel` | sqlalchemy raw |
| UI/demos | `gradio` | streamlit |
| Numerics | `numpy` | manual math |
| MCP servers | `fastmcp` | raw MCP protocol |

## Project Structure

- Use `pyproject.toml` for all project metadata and dependencies
- Place source code in a package directory matching the project name
- Use `uv` workspace members for monorepo sub-packages
- Run `uv run ruff check`, `uv run ruff format`, and `uv run --with ty==0.0.29 ty check` before committing

## Performance Conventions

1. Profile before optimizing — use `cProfile` or `py-spy` to find real bottlenecks
2. Prefer list comprehensions over `for` + `append` loops
3. Use generators / `yield` for large datasets to avoid memory spikes
4. Use `str.join()` instead of `+=` concatenation in loops
5. Use `dict` / `set` for membership tests instead of `list`
6. Use `functools.lru_cache` for expensive pure functions
7. Use `__slots__` on data classes instantiated at high volume
8. Batch database writes — avoid per-row commits
9. Prefer `asyncio` / `aiohttp` for I/O-bound concurrency; `multiprocessing` for CPU-bound
10. See `references/performance-tips.md` for profiling tool quick-reference

## Testing Conventions

1. Follow AAA (Arrange / Act / Assert) structure in every test
2. One behavior per test function — if the name needs "and", split it
3. Name tests: `test_<unit>_<scenario>_<expected_outcome>`
4. Use `pytest.raises(ExType, match=...)` for exception testing
5. Use `pytest.mark.parametrize` instead of copy-pasting test variants
6. Use fixtures (`conftest.py`) for shared setup; prefer narrow scope
7. Use `monkeypatch` over `unittest.mock.patch` for env vars and attributes
8. Use `tmp_path` fixture for file I/O tests
9. Use `freezegun` or `time-machine` for time-dependent tests
10. Use `@pytest.mark.slow` / `@pytest.mark.integration` markers and run with `-m`
11. Configure pytest in `pyproject.toml` under `[tool.pytest.ini_options]`
12. Set coverage thresholds: `--cov-fail-under=80`
13. See `references/testing-patterns.md` for fixture scope cheat sheet and conftest skeleton

## Critical Rules

1. Always use `uv` for package management — never `pip install` or `pip`
2. Use `uv add` to add dependencies — never `uv pip install`
3. Use `uv run --with ty==0.0.29 ty check` for type checking — never `mypy`
4. Run `uv run pytest` before committing any Python changes
5. Run `uv run ruff check` and `uv run ruff format` before committing
6. Check `references/exceptions.md` before breaking any convention
7. Prefer libraries from the preferred table over their alternatives

**Canonical terms** (use these exactly):
- `uv` -- the required package manager and task runner
- `ty` -- the required type checker (not mypy)
- `uv run --with ty==0.0.29 ty check` -- the required type-check command
- `ruff` -- the required linter and formatter
- `pyproject.toml` -- the single source of project configuration
- `uv run` -- prefix for all Python command execution
