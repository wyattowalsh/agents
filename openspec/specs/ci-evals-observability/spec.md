# ci-evals-observability Specification

## Purpose
Define CI, evaluation, and observability gates for agent asset changes and release readiness evidence.
## Requirements
### Requirement: Conformance gates

The CI/evals/observability lane SHALL define validation gates for registries, skills, MCP smoke fixtures, adapter fixtures, docs truth, AI instructions, OpenSpec changes, and config-driven Python quality tooling (Ruff lint/format and Astral ty).

#### Scenario: Registry schema changes

- **GIVEN** registry schema files are modified
- **WHEN** CI runs
- **THEN** schema validation and golden fixtures must pass before merge.

#### Scenario: Gated Python changes run config-driven Ruff and ty

- **GIVEN** a pull request touches gated Python sources declared in root `pyproject.toml`
- **WHEN** CI runs the Python quality job
- **THEN** CI SHALL run `uv run ruff check`, `uv run ruff format --check`, and `uv run ty check` without path-list arguments
- **AND** the commands SHALL resolve scope exclusively from `[tool.ruff]` and `[tool.ty]` in `pyproject.toml`.

#### Scenario: Portable skill scripts are Ruff-gated

- **GIVEN** a pull request touches `skills/**/scripts/**/*.py`
- **WHEN** CI runs `uv run ruff check`
- **THEN** those portable skill script paths SHALL be included via `[tool.ruff].include`
- **AND** ty SHALL remain scoped to repo-owned typed packages (`wagents`, `scripts`, `tests`, `skills/skill-creator/scripts`, `skills/nerdbot`) unless a follow-up change expands ty overrides.

#### Scenario: Pre-commit mirrors CI Python gates

- **GIVEN** a contributor runs pre-commit on Python files
- **WHEN** Ruff and ty hooks execute
- **THEN** hook entrypoints SHALL invoke config-driven `ruff check`, `ruff format`, and `ty check` aligned with CI and Makefile targets.

