# cursor-harness Specification

## Purpose
Define Cursor harness requirements for editor, CLI, Cloud Agent, cloud subagent, Bugbot, and ACP surfaces without fabricating support across distinct runtimes or mutating user/dashboard state.
## Requirements
### Requirement: Cursor harness projection

The Cursor harness lane SHALL define repo-owned Cursor editor and CLI projections for rules, skills, subagents, MCP, hooks, permissions, CLI config, Bugbot rules, and rollback fixtures, while documenting Cloud Agent, cloud subagent, Bugbot Admin API, and ACP boundaries.

#### Scenario: Cursor projection is validated

- **GIVEN** a Cursor adapter fixture exists
- **WHEN** validation runs
- **THEN** generated paths and support tiers match registry records.

#### Scenario: Cursor MCP uses project-safe interpolation

- **GIVEN** repo sync renders `.cursor/mcp.json`
- **WHEN** the MCP registry enables MCPHub
- **THEN** the rendered config includes only the managed `harness` MCPHub group by default
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
- **AND** the Cursor frontmatter includes explicit `readonly` and `model: cursor-grok-4.5-high` values.

#### Scenario: Cursor Cloud and API surfaces are caveated

- **GIVEN** support registries are validated
- **WHEN** Cursor Cloud Agent, cloud subagent, Bugbot, or ACP support is described
- **THEN** dashboard/team MCP, OAuth, secrets, Bugbot Admin API, and Cloud Agent settings are documented as out of scope for repo sync.

### Requirement: Cursor Grok 4.5 High pin

The Cursor harness SHALL force `cursor-grok-4.5-high` on every controllable Task/subagent path (overlay, rule, hooks, home projection) without mutating Cloud/dashboard state. Local CLI `exploreSubagentModel: inherit` and IDE High picker are operator SHOULD (user-owned). Sync SHALL NOT write `~/.cursor/cli-config.json` or live `state.vscdb`. Soft-rule omit ban (agents must not omit Task `model`) does not change Phase B omit-allow semantics.

#### Scenario: Task launches must pass High

- **GIVEN** a parent agent launches Cursor `Task` or a custom subagent
- **WHEN** the tool call is issued
- **THEN** it MUST pass `model: cursor-grok-4.5-high`
- **AND** soft rule requires agents SHALL NOT omit `model` or pass `inherit`, `*-fast`, or other non-pin slugs
- **AND** Phase B still allows omit so the High parent can inherit.

#### Scenario: Home sync copies allowlisted rules without orphan deletes

- **GIVEN** home sync runs with `--platforms cursor` (or shared)
- **WHEN** rules are projected to `~/.cursor/rules/`
- **THEN** allowlisted rules including `cursor-models.mdc` are copied from the repo
- **AND** home-only orphan `.mdc` files SHALL NOT be deleted.

#### Scenario: Home agents use managed-marker projection

- **GIVEN** portable agents have Cursor overlays pinned to `cursor-grok-4.5-high`
- **WHEN** home sync projects agents
- **THEN** managed agents are written to `~/.cursor/agents/` with the wagents managed marker
- **AND** unmarked user agents under that directory are preserved.

#### Scenario: Local app uses CLI inherit and IDE High without vscdb edits

- **GIVEN** local Cursor app/CLI config is in scope
- **WHEN** parent/Explore defaults are set
- **THEN** operators SHOULD set `~/.cursor/cli-config.json` `exploreSubagentModel: inherit`
- **AND** operators SHOULD set the IDE model picker to Grok 4.5 High
- **AND** sync SHALL NOT write `~/.cursor/cli-config.json` or live `state.vscdb`
- **AND** operators SHALL NOT hand-edit live `state.vscdb`.

#### Scenario: Hooks rewrite Task and deny non-allowlist subagents

- **GIVEN** Cursor hooks are rendered from the hook registry
- **WHEN** a `preToolUse` Task launch omits or mis-sets `model`
- **THEN** Phase A rewrite sets `updated_input.model` to `cursor-grok-4.5-high` (fail-open)
- **AND** Phase B `subagentStart` denies explicit models outside the High allowlist
- **AND** Phase B allows omit (inherit High parent).

