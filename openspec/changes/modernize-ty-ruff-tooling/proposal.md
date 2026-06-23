## Summary

Centralize Ruff and ty configuration in root `pyproject.toml`, unify Makefile/CI/pre-commit/agent
instructions to config-driven commands, include `tests/` in ty with overrides, adopt production
plus preview Ruff rules via staged rollout, and add doctor plus parity tests to prevent path-list
regression.

## Problem

Python quality gates duplicate path lists across Makefile, CI, pre-commit, and agent instructions.
Twelve top-level `scripts/*.py` files are outside CI Ruff scope. ty excludes tests. Hooks hard-code
narrower ty paths than pyproject. `wagents doctor` does not validate Ruff/ty pins or config.

## Proposed Change

- Declare gated Python scope in `[tool.ruff]` and `[tool.ty]` (SSOT).
- Run `uv run ruff check`, `uv run ruff format --check`, and `uv run ty check` without path args.
- Bump ty to latest stable pin; align Ruff `required-version` and pre-commit rev with lockfile.
- Stage Ruff preview after production-rule baseline is green.
- Fix violations across ~170 gated files using parallel ownership packages.
- Add `tests/test_python_tooling_config.py` and doctor checks for tooling health.

## Non-Goals

- Lint or type-check all 129 portable `skills/*/scripts` trees (optional follow-up wave).
- Introduce mypy.
- Change Python `requires-python` for nerdbot standalone installs.