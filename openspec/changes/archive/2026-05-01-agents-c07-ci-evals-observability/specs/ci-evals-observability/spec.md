## ADDED Requirements

### Requirement: Conformance gates

The CI/evals/observability lane SHALL define validation gates for registries, skills, MCP smoke fixtures, adapter fixtures, docs truth, AI instructions, and OpenSpec changes.

#### Scenario: Registry schema changes

- **GIVEN** registry schema files are modified
- **WHEN** CI runs
- **THEN** schema validation and golden fixtures must pass before merge.
