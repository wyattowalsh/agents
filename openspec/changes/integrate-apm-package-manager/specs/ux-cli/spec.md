# ux-cli Delta

## ADDED Requirements

### Requirement: wagents apm materialize projects repo SSOT into APM layout

The `wagents apm` command group SHALL materialize canonical repo assets from `agents/`, `instructions/`, and hook registries into `.apm/` and SHALL maintain `apm.yml` without duplicating repo-owned MCP registry entries.

#### Scenario: Maintainer refreshes APM primitives

- **GIVEN** the repository contains validated agents and instructions under their canonical paths
- **WHEN** a maintainer runs `uv run wagents apm materialize`
- **THEN** `.apm/agents/*.agent.md` and `.apm/instructions/*.instructions.md` SHALL be regenerated from repo SSOT
- **AND** `apm.yml` SHALL remain present with managed compilation markers
- **AND** repo MCP ownership SHALL stay under `config/mcp-registry.json` and MCPHub projections rather than APM lock reconciliation.

#### Scenario: Automation checks APM surface health

- **GIVEN** `apm.yml`, `.apm/`, and `opencode.json` exist in the repository
- **WHEN** a maintainer runs `uv run wagents apm doctor`
- **THEN** the command SHALL verify `opencode.json` retains `plugin`, `model`, `instructions`, and `skills.paths`
- **AND** the command SHALL report whether `.apm/` contains generated agents and instructions
- **AND** failures SHALL include actionable remediation hints.
