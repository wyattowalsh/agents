## ADDED Requirements

### Requirement: RTK fleet integration is doctor-verified and dry-run first

The repository SHALL provide a repo-owned RTK policy map and CLI doctor that distinguish RTK binary availability, RTK command capability, local harness posture, and unsupported surfaces.

#### Scenario: Automation checks RTK readiness

- **WHEN** `uv run wagents rtk doctor --format json` runs
- **THEN** it SHALL emit machine-readable `ok`, `summary`, and `checks` fields
- **AND** it SHALL include non-fatal warning rows for harnesses where RTK is available but not locally installed.

#### Scenario: Fleet sync is previewed

- **WHEN** `uv run wagents rtk sync --dry-run --format json` runs
- **THEN** it SHALL emit the planned RTK init commands from `config/rtk-integration.json`
- **AND** it SHALL not write local harness files.

#### Scenario: Fleet sync is applied

- **WHEN** `uv run wagents rtk sync --apply` runs
- **THEN** it SHALL execute only RTK init commands for selected supported harnesses
- **AND** it SHALL set repo-declared RTK telemetry environment variables for child processes
- **AND** it SHALL skip repo-deferred custom commands such as Grok shims until an implementation exists.

### Requirement: RTK ownership boundaries preserve repo-generated surfaces

The repository SHALL treat RTK-generated local files as user-owned local artifacts, not repo source.

#### Scenario: OpenCode RTK integration is configured

- **WHEN** RTK is enabled for OpenCode
- **THEN** RTK SHALL own `~/.config/opencode/plugins/rtk.ts`
- **AND** repo `opencode.json` SHALL NOT include RTK in the `plugin` array.

#### Scenario: Shared instructions are regenerated

- **WHEN** instruction mirrors or generated docs are refreshed
- **THEN** shared instruction sources SHALL NOT include `@RTK.md`
- **AND** Codex/Crush prompt-level RTK awareness SHALL remain local or platform-scoped.

### Requirement: Research hooks support explicit implementation handoff

The repo-managed research prompt hook SHALL keep research sessions read-only for source files, while allowing an explicit implementation handoff prompt to clear stored active research state for that session.

#### Scenario: Research plan is approved for implementation

- **GIVEN** a prior `/research` prompt activated research hook state
- **WHEN** the user sends a non-research prompt with explicit implementation language such as "continue and fix"
- **THEN** the prompt hook SHALL mark the stored research state inactive
- **AND** the write guard SHALL no longer block source-file edits solely because of the prior research prompt.

#### Scenario: Research mode is forced by environment

- **GIVEN** `RESEARCH_SKILL_ACTIVE=1` or equivalent forced research state is set
- **WHEN** a write tool runs
- **THEN** the read-only guard SHALL still block source-file writes.
