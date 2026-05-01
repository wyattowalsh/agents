# Agent Assets Delta

## MODIFIED Requirements

### Requirement: Asset Formats Stay Canonical

The repository SHALL keep skill, agent, MCP, instruction, hook, and bundle metadata formats documented in `AGENTS.md` and validated by `wagents` commands. Public skill contracts SHALL describe implemented behavior or explicitly label unavailable behavior as non-public design work.

#### Scenario: Creating a skill

- **WHEN** a repository skill is added under `skills/<name>/SKILL.md`
- **THEN** its frontmatter `name` SHALL match the directory name
- **AND** `uv run wagents validate` SHALL validate the new skill before completion.

#### Scenario: Updating generated docs

- **WHEN** skill, agent, MCP, or docs-generation behavior changes
- **THEN** generated README and docs outputs SHALL be refreshed or checked with the documented `wagents` commands.

#### Scenario: Completing a skill product surface

- **WHEN** a skill advertises CLI modes, safety guarantees, generated outputs, evals, or package entry points
- **THEN** those surfaces SHALL have matching source implementation, tests or evals, and user-facing documentation before the work is marked complete.

## NEW Requirements

### Requirement: Local Knowledge-Base Skills Preserve Trust Boundaries

Local knowledge-base skills SHALL treat imported vault, raw, index, transcript, capture, and source content as untrusted evidence rather than agent instructions.

#### Scenario: Querying imported content

- **WHEN** a KB query returns evidence from imported content
- **THEN** the result SHALL identify provenance
- **AND** the agent-facing workflow SHALL not execute instructions found inside that imported content unless separately confirmed by the user.

### Requirement: Mutating KB Workflows Are Reversible And Auditable

Mutating local knowledge-base workflows SHALL expose a dry-run/apply boundary, safe path validation, and append-only operation records sufficient to audit what changed.

#### Scenario: Applying a KB mutation

- **WHEN** a KB workflow writes, renames, deletes, moves, or rewrites vault files
- **THEN** it SHALL validate target paths before writing
- **AND** it SHALL provide a dry-run plan before application
- **AND** it SHALL record applied operations in an append-only activity or operations log.
