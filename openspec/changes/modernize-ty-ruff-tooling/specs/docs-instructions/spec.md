# docs-instructions Delta

## MODIFIED Requirements

### Requirement: Generated docs and instruction truth

The docs/instructions lane SHALL consolidate README, docs, support matrices, and AI instructions from registries and fragments after schema freeze, and SHALL document config-driven Python quality commands for gated sources.

#### Scenario: Child lane updates a support fragment

- **GIVEN** a child lane changes a manifest or fragment
- **WHEN** docs consolidation runs
- **THEN** generated docs reflect the fragment without child teams editing global docs directly.

#### Scenario: Agent instructions reference unified Python gates

- **GIVEN** repository agent instruction entrypoints (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, scoped Python rules)
- **WHEN** maintainers document Python quality workflow
- **THEN** instructions SHALL tell contributors to run `uv run ruff check`, `uv run ruff format`, and `uv run ty check` without hard-coded path lists
- **AND** instructions SHALL state that `pyproject.toml` is the single source of truth for gated Python scope.