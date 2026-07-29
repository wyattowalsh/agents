# Spec Delta: downstream-tooling

## REMOVED Requirements

### Requirement: Supported Agent Mapping Is Stable

RV-006 removes the former stable-mapping requirement in full because its
supported universe admitted mappings for harnesses that the repository no
longer endorses. Replacement requirements below define the narrowed managed
and Skills CLI-native taxonomies without carrying forward Gemini CLI,
Antigravity, or GitHub Copilot compatibility.

#### Scenario: Legacy supported-agent mapping is retired

- **GIVEN** the base requirement can be read as preserving mappings for
  `gemini-cli`, `antigravity`, or `github-copilot`
- **WHEN** this change is applied
- **THEN** the prior `Supported Agent Mapping Is Stable` requirement SHALL be
  removed in full
- **AND** no replacement mapping SHALL endorse those retired harnesses.

## ADDED Requirements

### Requirement: Supported agent taxonomies are explicit after retirement

The repository SHALL define the managed harness set as exactly `claude-code`,
`codex`, `crush`, `cursor`, `grok`, and `opencode`, and SHALL define the Skills
CLI-native subset as exactly `claude-code`, `codex`, `crush`, `cursor`, and
`opencode`. MCP-only and hybrid clients SHALL be reported separately and SHALL
NOT inflate either count.

#### Scenario: Public support data is generated after retirement

- **WHEN** homepage, README, install, or support-matrix data is generated
- **THEN** managed-harness rows and counts SHALL equal the exact six-member set
- **AND** Skills CLI command targets SHALL equal the exact five-member subset
- **AND** MCP-only or hybrid clients SHALL retain explicit surface labels
  without being counted as managed or Skills CLI-native harnesses.

### Requirement: Curated target universe excludes removed harness ids

`external_skills.SUPPORTED_TARGET_AGENTS` SHALL reject `gemini-cli`,
`antigravity`, and `github-copilot`. Authoring records and generated public
install commands SHALL contain only the remaining supported target agents.

#### Scenario: Removed harness ids are rejected from curated targets

- **GIVEN** an authoring or catalog row lists `gemini-cli`, `antigravity`, or
  `github-copilot` as a target agent
- **WHEN** curated target validation runs
- **THEN** those ids SHALL be rejected
- **AND** generated public install commands SHALL omit them.

### Requirement: Crush MCP remains Gemini-shaped

Crush (and AITK reusing the crush filter) SHALL project MCP via
`render_flat_mcp(..., harness="crush")` as a flat map with
`type: stdio`, and SHALL NOT use `render_client_mcp` for Crush.

#### Scenario: Crush MCP projection stays Gemini-shaped

- **GIVEN** Crush MCP sync renders from the MCP registry
- **WHEN** the Crush filter projects servers
- **THEN** output SHALL use `render_flat_mcp(..., harness="crush")`
- **AND** entries SHALL be a flat map with `type: stdio`
- **AND** the path SHALL NOT call `render_client_mcp` for Crush.

#### Scenario: AITK reuses the Crush filter

- **GIVEN** AITK consumes the Crush-filtered MCP projection
- **WHEN** repository sync emits AITK MCP entries
- **THEN** every emitted entry SHALL be selected by the Crush filter
- **AND** every emitted entry SHALL use the flat `type: stdio` shape
- **AND** no Gemini CLI, Antigravity, or GitHub Copilot ownership SHALL be
  reintroduced.

### Requirement: Candidate MCP WIP coexistence

Surgical harness-ID stripping of shared registries SHALL preserve dirty
candidate MCP servers and `scripts/mcphub/wrappers/candidate-*` wrappers.

#### Scenario: Candidate MCP WIP rows survive harness-id stripping

- **GIVEN** shared registries contain candidate MCP servers or
  `scripts/mcphub/wrappers/candidate-*` wrappers
- **WHEN** surgical harness-ID stripping removes Gemini/Antigravity/Copilot ids
- **THEN** candidate MCP WIP entries and wrappers SHALL remain present
- **AND** unrelated dirty worktree candidate state SHALL NOT be deleted.

### Requirement: Retired harness artifacts are absent from active surfaces

RV-005 closure SHALL require that active source, authored metadata, fixtures,
generated projections, and managed home receipts do not retain endorsement of
Gemini CLI, Antigravity, or GitHub Copilot. Semantic cleanup SHALL be bounded
and SHALL preserve explicitly classified historical/change-control evidence
and unrelated keep-set content.

#### Scenario: Retirement cleanup is verified

- **WHEN** focused retirement tests and the bounded source/generated semantic
  scan run
- **THEN** active surfaces SHALL reject the retired managed IDs and
  `https://github.com/google/gemini-cli`
- **AND** the explicit historical/change-control allowlist, unrelated GitHub
  functionality, `gemini-api`, and candidate source names SHALL remain intact.

### Requirement: Retirement generation converges before closure

All source-driven docs, MCPHub, README, reconciliation, sync, and APM
projections SHALL be generated before the final APM lock check. Retirement
closure SHALL require the deployed-file paths and hashes in `apm.lock.yaml` to
match the final generated state.

#### Scenario: Final retirement generation finishes

- **WHEN** every scheduled generation pass has completed
- **THEN** `uv run wagents apm refresh-lock --check` SHALL exit successfully
- **AND** a passing earlier lock snapshot SHALL NOT be reused as final proof.
