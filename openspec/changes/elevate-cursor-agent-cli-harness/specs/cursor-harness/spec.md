# Delta: Cursor Agent CLI first-class harness

## ADDED Requirements

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
