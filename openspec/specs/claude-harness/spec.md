# claude-harness Specification

## Purpose
Define Claude Code and Claude Desktop harness requirements for plugin, skills, MCP, desktop config, rollback, and redaction evidence.
## Requirements
### Requirement: Claude harness projection

The Claude harness lane SHALL define Claude Code and Claude Desktop projections from canonical skills, MCP profiles, instructions, plugins, and rollback fixtures.

#### Scenario: Claude support is claimed

- **GIVEN** a Claude support claim is made
- **WHEN** the claim is validated
- **THEN** it is backed by support-tier data and lane-specific fixtures or marked validation-required.
