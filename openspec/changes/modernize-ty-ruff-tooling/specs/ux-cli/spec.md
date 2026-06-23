# ux-cli Delta

## ADDED Requirements

### Requirement: Doctor validates Python tooling health

`wagents doctor` SHALL report whether root `pyproject.toml` defines Ruff and ty configuration and whether `uv run ruff --version` and `uv run ty --version` succeed.

#### Scenario: Healthy clone passes tooling checks

- **GIVEN** a repository checkout with `[tool.ruff]` and `[tool.ty]` in `pyproject.toml`
- **AND** dev dependencies are synced with `uv sync`
- **WHEN** `wagents doctor --format json` runs
- **THEN** the output SHALL include `python-tooling-config`, `ruff-tooling`, and `ty-tooling` checks with `ok` status.

#### Scenario: Missing tooling config fails doctor

- **GIVEN** `pyproject.toml` lacks `[tool.ruff]` or `[tool.ty]`
- **WHEN** `wagents doctor --format json` runs
- **THEN** `python-tooling-config` SHALL report `fail`
- **AND** overall doctor `ok` SHALL be false when required checks fail.