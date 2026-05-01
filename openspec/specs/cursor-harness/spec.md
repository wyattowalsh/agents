# cursor-harness Specification

## Purpose
Define Cursor harness requirements for editor, cloud-agent, and CLI surfaces without fabricating support across distinct runtimes.
## Requirements
### Requirement: Cursor harness projection

The Cursor harness lane SHALL define Cursor editor and agent projections for rules, skills, MCP profiles, and rollback fixtures.

#### Scenario: Cursor projection is validated

- **GIVEN** a Cursor adapter fixture exists
- **WHEN** validation runs
- **THEN** generated paths and support tiers match registry records.
