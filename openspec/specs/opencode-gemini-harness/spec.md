# opencode-gemini-harness Specification

## Purpose
Define OpenCode, Gemini CLI, and Antigravity harness requirements for model-neutral configuration, skills, MCP projection, and plugin placement.
## Requirements
### Requirement: OpenCode and Gemini projection

The OpenCode/Gemini lane SHALL preserve repo-managed OpenCode model-neutral policy while defining skills, MCP, plugin, and instruction projections.

#### Scenario: OpenCode plugin list changes

- **GIVEN** repo-managed OpenCode config is updated
- **WHEN** plugin entries are reviewed
- **THEN** npm plugin specs remain on `@latest` unless an explicit rollback is requested.
