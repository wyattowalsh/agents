## ADDED Requirements

### Requirement: MCP live-system justification

The MCP audit lane SHALL keep MCP servers only when live or dynamic external state is required and SHALL record transport, auth, secrets, sandbox, and smoke fixture requirements.

#### Scenario: Static MCP is identified

- **GIVEN** an MCP server only wraps static instructions or local deterministic scripts
- **WHEN** it is audited
- **THEN** the lane records a skill-replacement recommendation.
