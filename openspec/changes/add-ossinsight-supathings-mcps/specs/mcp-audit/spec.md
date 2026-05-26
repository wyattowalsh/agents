# mcp-audit Delta

## MODIFIED Requirements

### Requirement: MCP live-system justification

The MCP audit lane SHALL keep MCP servers only when live or dynamic external state is required and SHALL record transport, auth, secrets, sandbox, and smoke fixture requirements.

#### Scenario: Static MCP is identified

- **GIVEN** an MCP server only wraps static instructions or local deterministic scripts
- **WHEN** it is audited
- **THEN** the lane records a skill-replacement recommendation.

#### Scenario: Registry MCP accesses live external or local state

- **GIVEN** a managed registry MCP exposes live external data or local application data
- **WHEN** it is added to the normalized MCP registry
- **THEN** the change SHALL record the selected transport and package-manager launch command
- **AND** the change SHALL document any known auth, secret, rate-limit, local-data, or write-capability considerations in supporting MCP safety notes.
