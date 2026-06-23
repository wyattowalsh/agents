---
paths:
  - "**/*.py"
---
After modifying Python files, run `uv run ruff check --fix` on changed files. When you edit gated Python sources (see pyproject.toml `[tool.ruff].include` / `[tool.ty.src]`), also run `uv run ty check`.
