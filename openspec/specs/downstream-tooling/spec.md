# Downstream Tooling Specification

## Purpose

Define how this repository exposes the same asset bundle and OpenSpec workflows to supported downstream AI tools.
## Requirements
### Requirement: Supported Agent Mapping Is Stable

The repository SHALL maintain a deterministic mapping from repo-supported agent IDs to OpenSpec tool IDs and Skills CLI install targets, while documenting requested harness facets that do not have direct Skills CLI adapters.

#### Scenario: Installing curated external skills across supported harnesses

- **WHEN** a curated external skill command is added for global rollout
- **THEN** the command SHALL use only Skills CLI target IDs supported by the repo install/sync tooling
- **AND** desktop, cloud, or app UI harness facets without direct Skills CLI target IDs SHALL be reported as config or blind-spot surfaces rather than invented install adapters.

#### Scenario: Installing a user-requested local harness rollout

- **WHEN** a user explicitly requests installation across every locally installed client that supports Skills CLI adapters
- **THEN** the rollout command SHALL enumerate the current Skills CLI target IDs with observed local skill roots instead of using `--all`
- **AND** repo-managed sync MAY continue to target only the repository-supported agent set.

#### Scenario: Mapping split GitHub Copilot facets

- **WHEN** a user requests installation for GitHub Copilot web, CLI, or aggregate Copilot surfaces
- **THEN** the repository SHALL use the single `github-copilot` Skills CLI target for install/sync
- **AND** documentation or reports SHALL keep web and CLI audit facets separate when discussing observable surfaces and blind spots.

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
- **THEN** it SHALL run bundled preflight (`bash skills/grok-delegate/scripts/preflight.sh` or `scripts/doctor.py --format json`)
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

### Requirement: ChatGPT remote MCP handoff is stable and source-traceable

ChatGPT remote MCP access SHALL use the MCPHub public URL declared in local
MCPHub environment configuration and documented by repo-owned MCPHub docs.

#### Scenario: MCPHub tunnel reports the public URL

- **GIVEN** `MCPHUB_TUNNEL_ENABLED=true`
- **AND** `MCPHUB_PUBLIC_URL` is set
- **WHEN** MCPHub starts and passes its health check
- **THEN** the tunnel sidecar SHALL expose the same public `/mcp` URL for ChatGPT
- **AND** optional Zapier handoff SHALL report that public URL without including bearer tokens.

### Requirement: Chrome DevTools Source Ownership Is Singular Per Harness

Each supported harness SHALL have at most one active `chrome-devtools` MCP owner.

#### Scenario: Harness uses upstream plugin ownership

- **WHEN** a harness is marked as using the upstream Chrome DevTools plugin
- **THEN** repo sync SHALL NOT also project an active standalone `chrome-devtools` MCP entry into that harness
- **AND** the registry SHALL identify the source as `plugin`.

#### Scenario: Harness uses upstream extension ownership

- **WHEN** a harness is marked as using the upstream Chrome DevTools extension
- **THEN** repo sync SHALL NOT also project an active standalone `chrome-devtools` MCP entry into that harness
- **AND** the registry SHALL identify the source as `extension`.

#### Scenario: Harness lacks verified plugin support

- **WHEN** no concrete plugin or extension surface has been verified for a harness
- **THEN** the harness SHALL use `repo-mcp`, `manual-ui`, or `blind-spot` status
- **AND** documentation SHALL avoid claiming native plugin installation support.

### Requirement: Imported Chrome DevTools Skills Preserve Provenance

Imported Chrome DevTools skills SHALL retain clear provenance and local adaptation notes.

#### Scenario: A Chrome DevTools skill is promoted into `skills/`

- **WHEN** a skill derived from `ChromeDevTools/chrome-devtools-mcp` is added to the repository
- **THEN** its frontmatter SHALL include `license: Apache-2.0`
- **AND** its metadata SHALL identify `Google LLC` as upstream author and `0.23.0` as upstream package version
- **AND** its body or references SHALL include source URL, commit SHA, access date, and adaptation notes.

### Requirement: Chrome DevTools Runtime Artifacts Stay Out Of Version Control

Chrome DevTools workflows SHALL warn users away from committing runtime artifacts.

#### Scenario: A skill describes traces, screenshots, Lighthouse reports, heap snapshots, or browser profiles

- **WHEN** a promoted Chrome DevTools skill instructs the user to generate browser debugging artifacts
- **THEN** it SHALL include guidance to keep those artifacts local unless the user explicitly asks to save or share them
- **AND** generated runtime artifact paths SHALL NOT be added to committed source by default.

