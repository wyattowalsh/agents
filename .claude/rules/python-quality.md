---
paths:
  - "**/*.py"
---
After modifying Python files, run `uv run ruff check --fix` on changed files. When you edit code under `wagents/` or `scripts/`, also run `uv run --with ty==0.0.29 ty check`.
