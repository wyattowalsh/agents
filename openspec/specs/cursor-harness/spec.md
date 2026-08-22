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
- **AND** the Cursor frontmatter includes explicit `readonly` and `model: cursor-grok-4.6-xhigh` values.

#### Scenario: Cursor Cloud and API surfaces are caveated

- **GIVEN** support registries are validated
- **WHEN** Cursor Cloud Agent, cloud subagent, Bugbot, or ACP support is described
- **THEN** dashboard/team MCP, OAuth, secrets, Bugbot Admin API, and Cloud Agent settings are documented as out of scope for repo sync.

### Requirement: Cursor Grok 4.6 Extra High pin

The Cursor harness SHALL force `cursor-grok-4.6-xhigh` on every controllable Task/subagent path (overlay, rule, hooks, home projection) without mutating Cloud/dashboard state. Local CLI `exploreSubagentModel: inherit` and IDE Extra High picker are operator SHOULD (user-owned). Sync SHALL NOT write `~/.cursor/cli-config.json` or live `state.vscdb`. Soft-rule omit ban (agents must not omit Task `model`) does not change Phase B omit-allow semantics.

#### Scenario: Task launches must pass Extra High

- **GIVEN** a parent agent launches Cursor `Task` or a custom subagent
- **WHEN** the tool call is issued
- **THEN** it MUST pass `model: cursor-grok-4.6-xhigh`
- **AND** soft rule requires agents SHALL NOT omit `model` or pass `inherit`, `*-fast`, or other non-pin slugs
- **AND** Phase B still allows omit so the Extra High parent can inherit.

#### Scenario: Home sync copies allowlisted rules without orphan deletes

- **GIVEN** home sync runs with `--platforms cursor` (or shared)
- **WHEN** rules are projected to `~/.cursor/rules/`
- **THEN** allowlisted rules including `cursor-models.mdc` are copied from the repo
- **AND** home-only orphan `.mdc` files SHALL NOT be deleted.

#### Scenario: Home agents use managed-marker projection

- **GIVEN** portable agents have Cursor overlays pinned to `cursor-grok-4.6-xhigh`
- **WHEN** home sync projects agents
- **THEN** managed agents are written to `~/.cursor/agents/` with the wagents managed marker
- **AND** unmarked user agents under that directory are preserved.

#### Scenario: Local app uses CLI inherit and IDE Extra High without vscdb edits

- **GIVEN** local Cursor app/CLI config is in scope
- **WHEN** parent/Explore defaults are set
- **THEN** operators SHOULD set `~/.cursor/cli-config.json` `exploreSubagentModel: inherit`
- **AND** operators SHOULD set the IDE model picker to Grok 4.6 Extra High
- **AND** sync SHALL NOT write `~/.cursor/cli-config.json` or live `state.vscdb`
- **AND** operators SHALL NOT hand-edit live `state.vscdb`.

#### Scenario: Hooks rewrite Task and deny non-allowlist subagents

- **GIVEN** Cursor hooks are rendered from the hook registry
- **WHEN** a `preToolUse` Task launch omits or mis-sets `model`
- **THEN** Phase A rewrite sets `updated_input.model` to `cursor-grok-4.6-xhigh` (fail-open)
- **AND** Phase B `subagentStart` denies explicit models outside the Extra High allowlist
- **AND** Phase B allows omit (inherit Extra High parent).

### Requirement: Cursor Agent CLI is independently reviewable

The system SHALL treat `cursor-cli` as a first-class harness-master canonical
id for Cursor Agent CLI (`agent` / `cursor-agent`) without adding a Skills CLI
agent id and without inventing a second surface-registry product id.

#### Scenario: CLI aliases resolve to cursor-cli

- **WHEN** harness-master classifies `agent`, `cursor-agent`,
  `cursor-agent-cli`, `agent-cli`, or `cursor-cli`
- **THEN** the canonical harness list SHALL be `["cursor-cli"]`

#### Scenario: Editor aliases stay on cursor

- **WHEN** harness-master classifies `cursor`, `cursor-editor`,
  `cursor-desktop`, or `cursor-web`
- **THEN** the canonical harness list SHALL be `["cursor"]`

#### Scenario: All-order inserts cursor-cli after cursor

- **WHEN** harness-master runs `all`
- **THEN** deterministic order SHALL include `cursor` then `cursor-cli`
  then `grok-build`

#### Scenario: Skills CLI adapter remains cursor

- **WHEN** install or skills-sync guidance is emitted for Agent CLI
- **THEN** the Skills CLI agent name SHALL remain `cursor`
- **AND** `site_model.SUPPORTED_AGENTS` SHALL NOT gain `cursor-cli`

### Requirement: Cursor CLI projection is all-inclusive on shared SSOT

The `cursor-cli` harness-surface row SHALL declare projection surfaces covering
instructions, rules, skills, agents, hooks, mcp, plugins, cli-permissions, and
worktrees, while citing ACP as the existing `cursor-acp` row. Shared files SHALL
remain rendered once by the Cursor adapter.

#### Scenario: Surface row lists full CLI consumption

- **WHEN** `config/harness-surface-registry.json` is validated
- **THEN** `cursor-cli.projection_surfaces` SHALL include `instructions`,
  `rules`, `skills`, `agents`, `hooks`, `mcp`, `plugins`, `cli-permissions`,
  and `worktrees`

#### Scenario: Hooks are consumed not re-rendered

- **WHEN** hook-surface-registry describes `cursor-cli`
- **THEN** it SHALL point at `.cursor/hooks.json` and `~/.cursor/hooks.json`
- **AND** hook-registry render harness lists SHALL NOT gain `cursor-cli`

#### Scenario: Project CLI config stays permissions-only

- **GIVEN** repo sync renders `.cursor/cli.json`
- **THEN** the file SHALL contain project-level `permissions` only
- **AND** sync SHALL NOT write `~/.cursor/cli-config.json` or `state.vscdb`

#### Scenario: Plugin marketplace is operator-opt-in

- **WHEN** plugin posture for `cursor-cli` is documented
- **THEN** repo-owned plugin loading MAY use `--plugin-dir`
- **AND** `agent plugin marketplace add` SHALL NOT run during sync

### Requirement: Cursor CLI instruction overlay and doctor

The system SHALL provide a CLI-specific instruction overlay and a read-only
doctor that redacts account identifiers.

#### Scenario: Overlay is loadable

- **WHEN** Agent CLI starts in this repo
- **THEN** `instructions/cursor-cli-global.md` SHALL exist
- **AND** a thin `.cursor/rules/cursor-cli.mdc` pointer SHALL reference it

#### Scenario: Doctor redacts secrets and email

- **WHEN** `wagents cursor-cli doctor --format json` runs
- **THEN** output SHALL omit email, tokens, and API keys
- **AND** it MAY report binary version, model name, and cli-config key presence


### Requirement: Cursor Plannotator hooks are home-only

The system SHALL project Plannotator plan-review hooks into user
`~/.cursor/hooks.json` and copy `scripts/cursor/plannotator-plan-hook.py` to
`~/.cursor/hooks/plannotator-plan-hook.py`. Project `.cursor/hooks.json` SHALL
NOT gain Plannotator rows. `cursor-cli` SHALL consume the same user hooks and
SHALL NOT be added to hook-registry render lists.

#### Scenario: Home sync installs Cursor-native matchers

- **WHEN** Cursor home sync runs with Plannotator hooks enabled
- **THEN** `~/.cursor/hooks.json` SHALL contain flat `preToolUse` rows matching
  `SwitchMode` (enter / improve-context, timeout 5, `failClosed` false) and
  `CreatePlan` (plan review, timeout 345600, `failClosed` false)

#### Scenario: Project hooks stay fleet-only

- **WHEN** repo Cursor hook projection runs
- **THEN** git-tracked `.cursor/hooks.json` SHALL NOT include Plannotator
  CreatePlan or SwitchMode commands

#### Scenario: Cloud agents do not load user Plannotator hooks

- **WHEN** a Cursor cloud agent starts
- **THEN** it SHALL NOT load `~/.cursor/hooks.json`
- **AND** the 345600s review hook SHALL remain home-local so cloud runs cannot hang on it

#### Scenario: Opt-out skips Cursor Plannotator rows

- **WHEN** home sync runs with `--no-plannotator-hooks`
- **THEN** the Cursor shim SHALL NOT be copied
- **AND** Plannotator rows SHALL NOT be merged into `~/.cursor/hooks.json`

### Requirement: Cursor Plannotator shim is fail-open

The home shim SHALL parse Cursor camelCase and snake_case tool payloads, review
inline `plan` then `overview` on `CreatePlan`, and run `plannotator
improve-context` only when `SwitchMode` targets `plan`. Missing binary, empty
plan, crash, or unmapped JSON SHALL allow. The shim SHALL NOT exit 2 and SHALL
NOT scan other projects' plan files.

#### Scenario: CreatePlan deny maps to Cursor permission JSON

- **WHEN** Plannotator returns a mapped deny or block decision
- **THEN** the shim SHALL print `{"permission": "deny", "agent_message": "..."}`
  with optional `user_message`
- **AND** the process exit code SHALL be 0

#### Scenario: SwitchMode to agent allows immediately

- **WHEN** `SwitchMode` `target_mode_id` is not `plan`
- **THEN** the shim SHALL allow without invoking Plannotator
