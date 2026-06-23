# Downstream Tooling Delta

## ADDED Requirements

### Requirement: APM deploy complements wagents harness sync

The repository SHALL expose Microsoft APM as a complementary install path for supported harness targets while preserving wagents-owned sync for Grok, Crush, MCPHub, and OpenCode runtime plugins.

#### Scenario: Consumer installs bundle via APM

- **GIVEN** `apm.yml` and `apm.lock.yaml` are present at the repository root
- **WHEN** a consumer runs `apm install wyattowalsh/agents` or `apm install --only apm`
- **THEN** APM SHALL deploy agents, instructions, and hooks to supported harness directories
- **AND** Grok and Crush SHALL continue to rely on `wagents skills sync` and `scripts/sync_agent_stack.py` without APM target parity requirements in this change.

#### Scenario: OpenCode contract survives APM deploy

- **GIVEN** repo-managed `opencode.json` defines plugins, models, instructions, and `skills.paths`
- **WHEN** APM install or materialize updates harness artifacts
- **THEN** `wagents apm doctor` SHALL fail if `opencode.json` loses required keys
- **AND** repo sync SHALL not treat APM as the owner of OpenCode npm plugins, DCP, or ensemble configuration.

### Requirement: APM MCP stays separate from MCPHub

APM manifest MCP declarations SHALL NOT be treated as the canonical MCP registry for this repository.

#### Scenario: Audit checks APM lock consistency without MCP drift

- **GIVEN** repo MCP is owned by `config/mcp-registry.json` and MCPHub projections
- **WHEN** `apm audit --ci --no-drift` runs in CI
- **THEN** `apm.yml` SHALL not list MCP servers that are absent from `apm.lock.yaml`
- **AND** MCPHub-managed servers SHALL remain outside APM lock reconciliation.
