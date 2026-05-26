# mcp-audit Delta

## MODIFIED Requirements

### Requirement: MCP live-system justification

The MCP audit lane SHALL keep MCP servers only when live or dynamic external state is required and SHALL record transport, auth, secrets, sandbox, and smoke fixture requirements.

#### Scenario: MCPHub owns local MCP process routing

- **GIVEN** the repository enables MCPHub as the local MCP control plane
- **WHEN** managed local clients are rendered from the MCP registry
- **THEN** the registry SHALL preserve direct server definitions as MCPHub source material
- **AND** MCPHub settings SHALL expose all, group, and server MCP endpoints with bearer auth enabled
- **AND** tracked settings SHALL use environment placeholders instead of real secrets.

#### Scenario: Smart Routing remains opt-in

- **GIVEN** MCPHub Smart Routing requires PostgreSQL pgvector and embeddings
- **WHEN** the tracked MCPHub settings are generated
- **THEN** Smart Routing SHALL be disabled by default
- **AND** documentation SHALL require local database and embedding configuration before enabling smart endpoints.
