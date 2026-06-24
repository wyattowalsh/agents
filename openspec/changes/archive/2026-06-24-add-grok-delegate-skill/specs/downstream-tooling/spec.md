# Downstream Tooling Delta

## ADDED Requirements

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
