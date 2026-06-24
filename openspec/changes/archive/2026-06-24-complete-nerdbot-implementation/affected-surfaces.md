# Affected Surfaces

## Source Of Truth

- `skills/nerdbot/SKILL.md` — public skill contract and dispatch rules.
- `skills/nerdbot/AGENTS.md` — local development, safety, and compatibility rules.
- `skills/nerdbot/pyproject.toml` — package metadata, CLI entry point, extras, and package data.
- `skills/nerdbot/src/nerdbot/` — package implementation for CLI, contracts, safety, sources, evidence, retrieval, graph, watch, replay, research, and operations.
- `skills/nerdbot/scripts/` — compatibility entrypoints that should delegate to package primitives where possible.
- `skills/nerdbot/assets/` — starter vault templates and Obsidian-compatible page templates.
- `skills/nerdbot/references/` — public technical documentation and contracts.
- `skills/nerdbot/evals/` — Nerdbot skill eval cases.
- `tests/test_nerdbot*.py` — regression tests for package, CLI, contracts, scripts, safety, and workflows.
- `tests/test_package.py` and `tests/test_skill_creator_audit.py` — packaging and audit coverage that may need Nerdbot expectations updated.
- `openspec/changes/complete-nerdbot-implementation/` — change-control artifacts for this work.

## Generated Outputs

- `README.md` from `uv run wagents readme` when catalog-visible skill metadata changes.
- `docs/src/content/docs/skills/nerdbot.mdx` and `docs/src/generated-site-data.mjs` from `uv run wagents docs generate` after docs updates.
- Temporary package and KB fixture outputs created during tests or dry-run validation.

## Local-Only Or Ignored Outputs

- `skills/nerdbot/.venv/`, `__pycache__/`, `.DS_Store`, package ZIPs, generated SQLite indexes, graph JSONL/report files, and local vault data.
- Downstream generated OpenSpec tool artifacts unless explicitly promoted as repo-owned source.

## Validation Commands

- `uv run ruff check skills/nerdbot tests/`
- `uv run ruff format --check skills/nerdbot tests/`
- `uv run ty check`
- `uv run pytest tests/test_nerdbot*.py tests/test_package.py tests/test_skill_creator_audit.py -q`
- `uv run wagents validate`
- `uv run wagents eval validate`
- `uv run python skills/skill-creator/scripts/audit.py skills/nerdbot/ --format json`
- `uv run wagents package nerdbot --dry-run`
- `uv run wagents openspec validate`
- `git diff --check`
