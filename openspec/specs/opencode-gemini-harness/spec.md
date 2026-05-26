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

#### Scenario: OpenCode Ensemble inherits agent defaults

- **GIVEN** OpenCode Ensemble is enabled for team orchestration
- **WHEN** teammates are spawned without an explicit model override
- **THEN** Ensemble leaves its model fields empty so teammates inherit the repo-managed `openai/gpt-5.5` agent variants: `plan` on `xhigh`, and `build`, `explore`, and `general` on `high`.
