# cursor-harness Specification

## Purpose
Define Cursor harness requirements for editor, CLI, Cloud Agent, cloud subagent, Bugbot, and ACP surfaces without fabricating support across distinct runtimes or mutating user/dashboard state.

## Requirements
### Requirement: Cursor harness projection

The Cursor harness lane SHALL define repo-owned Cursor editor and CLI projections for rules, skills, subagents, MCP, hooks, permissions, CLI config, Bugbot rules, and rollback fixtures.

#### Scenario: Cursor projection is validated

- **GIVEN** a Cursor adapter fixture exists
- **WHEN** validation runs
- **THEN** generated paths and support tiers match registry records.

#### Scenario: Cursor MCP uses project-safe interpolation

- **GIVEN** repo sync renders `.cursor/mcp.json`
- **WHEN** the MCP registry enables MCPHub
- **THEN** the rendered config includes only the managed `harness-safe` MCPHub group by default
- **AND** secrets use `${env:NAME}` placeholders
- **AND** repo paths use `${workspaceFolder}`.

#### Scenario: Cursor permissions do not override UI allowlists by default

- **GIVEN** repo sync renders `.cursor/permissions.json`
- **WHEN** no source config explicitly opts into Cursor allowlist overrides
- **THEN** the file may include `autoRun.block_instructions`
- **AND** it SHALL NOT include `mcpAllowlist`
- **AND** it SHALL NOT include `terminalAllowlist`.

#### Scenario: Cursor CLI project config stays project-scoped

- **GIVEN** repo sync renders `.cursor/cli.json`
- **WHEN** the file is validated
- **THEN** it contains project-level `permissions`
- **AND** it SHALL NOT include global-only CLI fields.

#### Scenario: Cursor subagents are explicit overlays

- **GIVEN** portable agents exist in `agents/*.md`
- **WHEN** repo sync renders `.cursor/agents/*.md`
- **THEN** every portable agent has a matching `config/cursor-agents.json` overlay
- **AND** the Cursor frontmatter includes explicit `readonly` and `model: inherit` values.

#### Scenario: Cursor Cloud and API surfaces are caveated

- **GIVEN** support registries are validated
- **WHEN** Cursor Cloud Agent, cloud subagent, Bugbot, or ACP support is described
- **THEN** dashboard/team MCP, OAuth, secrets, Bugbot Admin API, and Cloud Agent settings are documented as out of scope for repo sync.
