# Downstream Tooling Delta

## ADDED Requirements

### Requirement: Token efficacy program governs layered tool adoption with research gates

The repository SHALL treat token-efficacy tooling as layered, non-stacking categories with compare research, explicit decision gates, and measured apply steps before any new third-party OSS install.

#### Scenario: Category compare completes before install recommendation

- **WHEN** a maintainer runs Wave 1 research for a missing token layer
- **THEN** the program SHALL produce a decision matrix with winner, runner-up, rationale, and non-stacking notes versus existing RTK and OpenCode DCP
- **AND** SHALL NOT recommend installing Sleev, Headroom, Cozempic, mcp-compressor, jCodeMunch, or similar tools until decision gates approve that category.

#### Scenario: One primary tool per layer

- **GIVEN** RTK owns shell dedup and OpenCode DCP owns session pruning for OpenCode
- **WHEN** a new layer winner is approved
- **THEN** maintainers SHALL install at most one primary tool for that layer
- **AND** SHALL measure overlap with `wagents rtk gain` and DCP stats before stacking additional tools.

### Requirement: RTK fleet live apply follows doctor verification and telemetry policy

The token efficacy program SHALL extend `integrate-rtk-harness-fleet` Wave 4 by applying RTK to supported harnesses only after doctor success and explicit maintainer approval.

#### Scenario: RTK doctor gates live apply

- **WHEN** Wave 2 RTK live apply is requested
- **THEN** `uv run wagents rtk doctor --format json` SHALL run first
- **AND** live apply SHALL be blocked when doctor reports fail status for required checks.

#### Scenario: Fleet sync apply uses telemetry-disabled init

- **WHEN** `RTK_TELEMETRY_DISABLED=1 uv run wagents rtk sync --apply --platforms claude-code,cursor,opencode,codex,gemini-cli,github-copilot` runs with maintainer approval
- **THEN** it SHALL execute only RTK init commands from `config/rtk-integration.json`
- **AND** SHALL set repo-declared RTK telemetry environment variables for child processes
- **AND** SHALL skip repo-deferred custom commands such as Grok shims until T041 schema proof exists.

#### Scenario: Post-apply savings are measured

- **WHEN** RTK live apply completes successfully
- **THEN** maintainers SHALL capture `uv run wagents rtk gain --graph` (and `rtk gain --history` when T044 lane exists) as baseline evidence for later stacking decisions.

### Requirement: OpenCode DCP tuning remains model-neutral and evidence-gated

The program SHALL tune OpenCode DCP only when Wave 1 R5 log review shows compaction pain or threshold mismatch.

#### Scenario: DCP tune is conditional

- **GIVEN** R5 DCP log and stats review finds no compaction pain
- **WHEN** Wave 4 executes
- **THEN** the program SHALL skip edits to `config/opencode-dcp.jsonc`.

#### Scenario: DCP stays model-neutral when tuned

- **WHEN** Wave 4 edits `config/opencode-dcp.jsonc`
- **THEN** the config SHALL NOT add `compress.modelMaxLimits` or `compress.modelMinLimits` unless the user explicitly requests per-model context limits.

## MODIFIED Requirements

### Requirement: RTK fleet integration is doctor-verified and dry-run first

The repository SHALL provide a repo-owned RTK policy map and CLI doctor that distinguish RTK binary availability, RTK command capability, local harness posture, and unsupported surfaces. The token efficacy program SHALL complete Wave 4 rollout tasks T040–T044 from `integrate-rtk-harness-fleet` including optional `scripts/sync_agent_stack.py --with-rtk`, Grok RTK shim after schema proof, public docs/catalog surfacing, shared-corpus `@RTK.md` validation, and `rtk gain --history` review lane.

#### Scenario: Stack sync can opt into RTK projection

- **WHEN** a maintainer runs `uv run python scripts/sync_agent_stack.py --apply --targets repo --with-rtk` or sets `RTK_ENABLED=1`
- **THEN** stack sync SHALL invoke or surface RTK sync planning consistent with `config/rtk-integration.json`
- **AND** SHALL preserve dry-run as the default when `--with-rtk` is omitted.

#### Scenario: Shared instructions remain free of RTK includes

- **WHEN** instruction mirrors or generated docs are refreshed during Wave 3
- **THEN** shared instruction sources SHALL NOT include `@RTK.md`
- **AND** validation (T043) SHALL detect new shared-corpus `@RTK.md` references.
