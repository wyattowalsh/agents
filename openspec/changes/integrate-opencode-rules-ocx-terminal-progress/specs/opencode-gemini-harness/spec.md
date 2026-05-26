# OpenCode Gemini Harness Delta

## MODIFIED Requirements

### Requirement: OpenCode and Gemini projection

The OpenCode/Gemini lane SHALL preserve repo-managed OpenCode model-neutral policy while defining skills, MCP, plugin, and instruction projections.

#### Scenario: OpenCode plugin list changes

- **GIVEN** repo-managed OpenCode config is updated
- **WHEN** plugin entries are reviewed
- **THEN** npm plugin specs remain on `@latest` unless an explicit rollback is requested
- **AND** npm runtime plugins that affect prompt context or terminal UX SHALL be documented in repo OpenCode plugin notes.

#### Scenario: OCX-managed components remain outside runtime plugin config

- **GIVEN** OCX-managed components are present under `.opencode/` with receipts under `.ocx/`
- **WHEN** OpenCode runtime plugin entries are updated
- **THEN** OCX itself SHALL NOT be added to `opencode.json`
- **AND** OCX-managed component package names SHALL NOT be added as bare runtime plugins unless the user explicitly chooses that package path over the component path.

#### Scenario: Rule injection avoids duplicated always-loaded instructions

- **GIVEN** `opencode-rules` is enabled as a runtime plugin
- **WHEN** repo or user rule files are documented or added
- **THEN** broad always-on repo policy SHALL remain in canonical instruction files
- **AND** OpenCode rule files SHOULD be reserved for conditional path, prompt, tool, command, project, branch, operating-system, or CI-specific guidance.
