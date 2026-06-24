# MCP Audit Delta

## MODIFIED Requirements

### Requirement: MCPHub owns local MCP process routing

The repository SHALL keep MCPHub as the process owner for managed local MCP servers while preserving registry-derived settings and secret-free tracked configuration.

#### Scenario: MCPHub exposes a harness-safe group

- **GIVEN** the repository enables MCPHub as the local MCP control plane
- **WHEN** tracked MCPHub settings are generated or reviewed
- **THEN** the `harness-safe` group SHALL include only the approved harness server set
- **AND** the group SHALL be exposed through the `/mcp/harness-safe` route with bearer auth still enabled.
