# Docs And Instructions Spec Delta — Things++

## ADDED Requirements

### Requirement: Things++ documentation is generated from canonical capability truth

Current MCPHub/operator, skill catalog/research, ChatGPT bundle, KB source, README, and public web documentation SHALL agree with the canonical single-group topology and generated Things++ capability ledger.

#### Scenario: Documentation generation runs

- **WHEN** skill, registry, or capability inputs change
- **THEN** maintainers SHALL run the repository web/catalog/README generators and checks
- **AND** SHALL NOT hand-edit generated catalog/index pages
- **AND** SHALL invoke `docs-steward` when available and record its finding or blocker.

### Requirement: ChatGPT setup docs preserve platform boundaries

`platforms/chatgpt/things-plus-plus/` SHALL document the exact endpoint, built-in MCPHub OAuth scopes, complete tool scan, client/tool approvals, refresh/revocation checks, read/write/destructive test prompts, emergency disablement, account/workspace limits, unsupported capabilities, and manual gates. Its canonical human-facing filenames SHALL be exactly `README.md`, `PROJECT_INSTRUCTIONS.md`, `APP_SETUP.md`, `TEST_PROMPTS.md`, `SAFETY.md`, and generated `CAPABILITY_MATRIX.md`; machine contracts SHALL use `bundle.json`, `bundle.schema.json`, `registration-reference.json`, `registration-reference.schema.json`, `observed-wire-record.template.json`, and `observed-wire-record.schema.json`; validation SHALL use `validate_bundle.py` and `test_validate_bundle.py`.

#### Scenario: Readers follow the ChatGPT instructions

- **WHEN** a maintainer configures the connector
- **THEN** the only MCP URL SHALL be `https://mcp.w4w.dev/mcp/things`
- **AND** the instructions SHALL NOT claim ChatGPT loads the portable skill, expose a direct server route, use a generic tunnel group, or weaken destructive confirmation.

### Requirement: Completion reports separate proof layers

The Things++ migration report SHALL distinguish source, generated repository, root plugin artifact, installed client, live MCPHub, live Things reads, remote OAuth/tunnel, and ChatGPT UI evidence.

#### Scenario: A later proof layer is unavailable

- **GIVEN** earlier static or local layers pass
- **WHEN** an installed/live/remote/UI layer is unrun or blocked
- **THEN** the report SHALL label that layer separately with the exact reason and next action
- **AND** SHALL NOT promote earlier evidence into a claim about the missing layer.

#### Scenario: F0 live prerequisites are reported

- **GIVEN** both fixed Shortcuts are absent, TCC readiness is unproven, and current runtime evidence is temporally inconsistent/stale
- **WHEN** source progress or readiness is reported
- **THEN** the report SHALL say source work and local bearer schema/catalog activation may proceed after fresh coherent provenance, while affected calls remain typed unavailable/degraded and are not operational
- **AND** SHALL say remote/public activation remains blocked on fresh fixed-bridge, noninteractive-TCC, OAuth, ingress, and observed-wire proof.

#### Scenario: Current remote continuation is authorized

- **WHEN** the local J4 barrier passes and the explicitly authorized S4/F5 continuation begins
- **THEN** the report SHALL distinguish remote source/offline proof, capture listener, observed ChatGPT wire, production OAuth origin, Cloudflare tunnel, external conformance, and ChatGPT UI readback
- **AND** SHALL label missing TCC, observed-wire, or UI evidence as blocked or unrun for that layer rather than `not authorized`
- **AND** SHALL NOT claim a public endpoint, durable tunnel, app, Project, or UI state from source or offline proof alone.

### Requirement: Private task content is excluded from documentation and evidence

Documentation, eval fixtures, capability manifests, test logs, and migration reports SHALL use synthetic values or status/count/schema evidence only.

#### Scenario: A live read is used for assurance

- **WHEN** a bounded Inbox, Today, project, or tag probe runs
- **THEN** retained evidence SHALL include only redacted status, counts, schema/tool IDs, and pass/fail results
- **AND** SHALL NOT persist titles, notes, checklists, tags, or other private content.

### Requirement: Generated Things documentation has one ownership chain

The ownership chain SHALL be portable skill source and canonical capability ledger, then catalog authoring sync, then web/catalog/README generation; generated MDX/index pages SHALL never be hand-edited.

#### Scenario: Skill or capability source changes

- **WHEN** maintainers update Things Manager or `capability-manifest.json`
- **THEN** they SHALL run authoring sync and `uv run python skills/things-manager/scripts/render_capabilities.py --check` before web/catalog/README checks
- **AND** generated diffs SHALL be owned by the serialized generation barrier.
