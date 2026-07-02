# Docs Instructions Delta

## ADDED Requirements

### Requirement: Maintainer docs describe token layer taxonomy and decision gates

The repository SHALL publish a token efficacy maintainer hub that documents context layers, current owners, research gates, and pointers to RTK, OpenCode DCP, and MCPHub posture without bloating always-loaded instruction tokens.

#### Scenario: AGENTS.md documents token posture

- **WHEN** Wave 3 docs-steward completes
- **THEN** `AGENTS.md` SHALL include a concise token budget section covering layer taxonomy, one-tool-per-layer rule, decision gates, and links to harness-config docs
- **AND** SHALL NOT embed `@RTK.md` or vendor local RTK paths into shared instruction bridges.

#### Scenario: Harness-config hub documents token layers

- **WHEN** Wave 3 docs-steward completes
- **THEN** the docs site SHALL include a harness-config token posture page describing shell (RTK), session (DCP), MCP (MCPHub groups / R2 outcome), standing context (R3 trim list), and landscape tracking (R4 journal workflow)
- **AND** generated docs SHALL be produced via `uv run wagents docs generate --no-installed` and validated with `uv run wagents docs build`.

#### Scenario: Standing context trim is evidence-backed

- **GIVEN** Wave 1 R3 produces trim candidates for skills, rules, and descriptions
- **WHEN** maintainers apply standing-context reductions
- **THEN** edits SHALL reference R3 evidence
- **AND** SHALL preserve progressive disclosure (scoped rules and on-demand skill bodies) rather than deleting safety or clarification-gate policy from `instructions/global.md`.

## MODIFIED Requirements

### Requirement: Progressive disclosure token budget is documented for maintainers

The repository instruction architecture SHALL document approximate always-loaded token costs and the research → decision → apply → docs pipeline for token tooling so maintainers can audit context growth without reading local research journals.

#### Scenario: Token budget table is current

- **WHEN** Wave 3 regenerates README and docs
- **THEN** maintainer-facing docs SHALL list baseline always-loaded surfaces (for example `global.md`, skill descriptions) and note that research journals under `~/.claude/research/` are local evidence, not repo SSOT
- **AND** `uv run wagents readme --check` SHALL pass after publication.
