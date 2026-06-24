# Downstream Tooling Specification

## Purpose

Define how this repository exposes the same asset bundle and OpenSpec workflows to supported downstream AI tools.
## Requirements
### Requirement: Supported Agent Mapping Is Stable

The repository SHALL maintain a deterministic mapping from repo-supported agent IDs to OpenSpec tool IDs.

#### Scenario: Generating OpenSpec artifacts for repo-supported tools

- **WHEN** a user runs `uv run wagents openspec init --apply`
- **THEN** the command SHALL configure OpenSpec tools for the supported repo agents by default
- **AND** the command SHALL expose an option to pass raw OpenSpec tool IDs for tools outside the repo support matrix.

### Requirement: JSON Interfaces Are Preferred For Automation

Automation SHALL consume OpenSpec JSON commands instead of scraping markdown or terminal UI output.

#### Scenario: An AI tool needs current change status

- **WHEN** the tool needs artifact completion state for a change
- **THEN** it SHALL use `uv run wagents openspec status --change <name> --format json` or the equivalent `openspec status --json` command.

#### Scenario: An AI tool needs next-step instructions

- **WHEN** the tool needs instructions for a planning or implementation artifact
- **THEN** it SHALL use `uv run wagents openspec instructions <artifact> --change <name> --format json` or the equivalent `openspec instructions --json` command.

### Requirement: Grok Build harness has a repo-owned policy template

The repository SHALL provide a sanitized Grok policy source at `config/grok-config.toml` and merge it into `~/.grok/config.toml` while preserving user-owned TOML tables outside the managed ownership set.

#### Scenario: Home Grok config merge preserves user extensions

- **GIVEN** `~/.grok/config.toml` contains a non-owned table `[user_custom]`
- **WHEN** home sync runs with `--platforms grok`
- **THEN** the `[user_custom]` table SHALL remain in the merged output
- **AND** managed MCP and policy blocks SHALL be replaced from repo sources
- **AND** sync SHALL refuse to apply if non-owned user tables would be dropped.

#### Scenario: Blend-owned tables preserve user-only keys

- **GIVEN** `~/.grok/config.toml` contains `[ui]` with `theme = "dark"` and repo policy sets `ui.yolo = true`
- **WHEN** home sync runs with `--platforms grok`
- **THEN** merged `[ui]` SHALL contain `theme = "dark"` from the user config
- **AND** `yolo = true` from repo policy SHALL override any prior user value for that key.

#### Scenario: Marker-less MCP reconciliation

- **GIVEN** Grok CLI rewrote `~/.grok/config.toml` and removed managed markers but left `mcp_servers` tables
- **WHEN** home sync runs with `--platforms grok`
- **THEN** sync SHALL strip registry-projected `mcp_servers.*` tables before re-appending the managed MCP block
- **AND** the result SHALL contain exactly one managed MCP projection per registry name.

#### Scenario: Project Grok config remains MCP-only

- **GIVEN** Grok project config may only carry MCP, plugins, and permission tables
- **WHEN** repo sync targets `.grok/config.toml`
- **THEN** the file SHALL contain only the managed MCP block from the registry
- **AND** full model/feature policy SHALL be written only to `config/grok-config.toml` and `~/.grok/config.toml`.

### Requirement: Grok skills install uses Claude Skills CLI alias

Because Skills CLI has no native `grok` adapter, `wagents install -a grok` and `wagents skills sync -a grok` SHALL install via the `claude-code` adapter and mirror global skills into `~/.grok/skills` when Grok is targeted.

#### Scenario: Install grok-targeted skills via alias

- **GIVEN** a user runs `wagents install review -a grok -y`
- **WHEN** the install subprocess invokes `npx skills add`
- **THEN** the agent flag SHALL be `claude-code`, not `grok`
- **AND** after success the CLI SHALL mirror missing skills into `~/.grok/skills`.

### Requirement: Grok home sync is isolatable from other harnesses

`sync_agent_stack.py` SHALL support a platform filter so Grok home config can be updated without merging OpenCode or other harness targets.

#### Scenario: Grok-only home sync skips OpenCode

- **GIVEN** OpenCode home merge would raise `ConfigDropError`
- **WHEN** sync runs with `--platforms grok --targets home`
- **THEN** only Grok adapter sync SHALL execute
- **AND** OpenCode config paths SHALL not be read or written.

### Requirement: Grok inventory includes project-local skills

When `REPO_ROOT/.grok/skills/` exists, installed-skill inventory for Grok SHALL scan that directory with scope `project` and prefer project paths over global duplicates for the same skill name.

#### Scenario: Repo project skills appear in Grok inventory

- **GIVEN** `REPO_ROOT/.grok/skills/demo-skill/SKILL.md` exists
- **WHEN** inventory queries the `grok` harness with `root=REPO_ROOT`
- **THEN** a row for `demo-skill` SHALL be returned with scope `project`
- **AND** if the same skill name exists globally, the project path SHALL win.

### Requirement: Platform adapters own harness-specific sync logic

Grok MCP and config merge logic SHALL live in `wagents/platforms/grok.py` and `scripts/sync_agent_stack.py` SHALL delegate to `sync_platform_repo_target("grok")` and `sync_platform_home_target("grok")` instead of inline `merge_grok_config`.

#### Scenario: Monolith delegates Grok sync to adapter

- **GIVEN** repo or home sync includes the grok platform
- **WHEN** sync targets are applied
- **THEN** `wagents/platforms/grok.py` SHALL perform render and merge
- **AND** monolith SHALL not duplicate `render_grok_mcp_block` after migration.

### Requirement: wagents is globally installable from Git

The repository SHALL support installing the `wagents` CLI globally via `uv tool install wagents --from git+https://github.com/wyattowalsh/agents` and SHALL resolve agents repository assets at runtime instead of assuming the package parent directory is the repo root.

#### Scenario: Global binary validates inside a clone

- **GIVEN** `wagents` is installed with `uv tool install`
- **AND** the user runs the command inside a checked-out agents repository
- **WHEN** the user runs `wagents validate`
- **THEN** the command SHALL discover the repo root from the working directory
- **AND** validation SHALL execute against that repository's `skills/`, `agents/`, and related assets.

### Requirement: Grok Delegate Uses Native CLI Surfaces

The `grok-delegate` skill SHALL route cross-harness Grok Build delegation through the native Grok CLI and SHALL NOT introduce a parallel wrapper, MCP server, or hidden orchestration service.

#### Scenario: Parent dispatches a Grok task node

- **GIVEN** a parent harness has decomposed work into a bounded task graph
- **WHEN** a node is assigned to Grok Build through `grok-delegate`
- **THEN** the delegated command SHALL use native `grok --no-auto-update -p ... --cwd ... --output-format json` or `grok -r <sessionId> -p ...` surfaces
- **AND** the parent harness SHALL retain ownership of the graph, dependencies, and synthesis.

#### Scenario: User asks to install or configure skills for Grok

- **WHEN** a request is about skill installation, sync, or harness configuration
- **THEN** `grok-delegate` SHALL route to the repo sync or harness stewardship flow instead of executing Skills CLI installs directly.

### Requirement: Grok Delegate Requires Preflight And Ledger Accounting

`grok-delegate` SHALL require machine-readable preflight and explicit session accounting before synthesis or dependent waves proceed.

#### Scenario: Grok delegation starts

- **WHEN** the parent prepares a Grok delegation wave
- **THEN** it SHALL run `uv run wagents grok doctor --format json`
- **AND** it SHALL stop or downshift the Grok lane when required checks fail.

#### Scenario: Delegated sessions complete

- **WHEN** a Grok delegation wave finishes
- **THEN** the parent SHALL record one terminal ledger row per delegated session before unblocking dependent work.

### Requirement: Grok Delegation Maintains Safety Boundaries

`grok-delegate` SHALL preserve repo safety policies for approval, write isolation, and live actions.

#### Scenario: Delegated task can mutate files

- **WHEN** a Grok command can edit files
- **THEN** the parent SHALL assign at most one writer per worktree
- **AND** the command SHALL use an explicit `--cwd`
- **AND** the command SHALL cap runaway work with `--max-turns` where available.

#### Scenario: Approval bypass is considered

- **WHEN** a delegation prompt or command proposes `--always-approve`
- **THEN** the default flow SHALL reject it unless the active user explicitly approved that bypass for the exact target and scope.

### Requirement: Grok Doctor Supports Machine-Readable Output

The repo Grok diagnostic surface SHALL support automation-safe JSON output for preflight gates.

#### Scenario: Automation runs Grok doctor

- **WHEN** `uv run wagents grok doctor --format json` runs
- **THEN** it SHALL emit a machine-readable result with required checks and statuses
- **AND** it SHALL exit nonzero when required checks fail.

