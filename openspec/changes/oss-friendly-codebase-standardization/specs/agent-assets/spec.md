# Agent Assets Delta

## MODIFIED Requirements

### Requirement: Asset Formats Stay Canonical

The repository SHALL keep skill, agent, MCP, instruction, hook, and bundle metadata formats documented in `AGENTS.md` and validated by `wagents` commands.

#### Scenario: Generated skill rows use a shared public contract

- **WHEN** repository docs or JSON indexes describe repo-owned, curated external, or installed external skills
- **THEN** each row SHALL expose a comparable public contract for name, description, source type, display source, install command, installability, trust tier, provenance or review state, supported agents where known, and knowledge inventory where applicable
- **AND** implementation-specific local paths SHALL not be required for readers to compare the rows.

#### Scenario: Cleanup preserves source ownership

- **WHEN** cleanup or production-readiness work classifies stale, generated, local-only, or source-of-truth artifacts
- **THEN** source-of-truth files SHALL be preserved unless the change explicitly updates their ownership
- **AND** generated or local-only artifacts SHALL be regenerated, ignored, or documented according to the repository source-of-truth rules
- **AND** unrelated dirty work SHALL not be deleted, reset, stashed, or overwritten.
