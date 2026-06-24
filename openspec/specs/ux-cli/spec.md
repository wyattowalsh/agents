# ux-cli Specification

## Purpose
Define CLI and UX output contracts for readable, actionable agent workflow status, validation, and error reporting.
## Requirements
### Requirement: CLI automation contracts

The UX/CLI lane SHALL define human-readable and machine-readable command output contracts for doctor, catalog, sync, rollback, audit, skill, MCP, and OpenSpec workflows.

#### Scenario: Automation consumes CLI output

- **GIVEN** an automation invokes a `wagents` command with JSON output
- **WHEN** the command succeeds or fails
- **THEN** it returns stable fields and actionable remediation hints.

### Requirement: Global wagents Discovers Repository Root At Runtime

The `wagents` CLI SHALL resolve the agents repository root at runtime for global installs (`uv tool install`) and editable checkouts, using `WAGENTS_REPO_ROOT`, `--repo-root`, cwd walk, and package-parent fallback.

#### Scenario: Global binary resolves repo assets

- **WHEN** `wagents` is invoked from outside a clone via a global install
- **THEN** it discovers the agents repository root before reading `skills/`, `config/`, or `scripts/`
- **AND** `wagents self doctor` reports the resolved root and install mode.

#### Scenario: Contributor uses editable checkout

- **WHEN** `uv run wagents` executes inside the repository
- **THEN** repo discovery SHALL prefer the checkout root without requiring `WAGENTS_REPO_ROOT`.

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

