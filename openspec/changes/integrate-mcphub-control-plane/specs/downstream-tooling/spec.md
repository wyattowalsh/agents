# Downstream Tooling Delta

## ADDED Requirements

### Requirement: MCPHub endpoint projection is source-traceable

Generated downstream tool artifacts SHALL be derived from canonical repo sources and SHALL document their owning source file or command.

#### Scenario: MCPHub client endpoints are projected

- **GIVEN** `mcphub.enabled` is true in the MCP registry
- **WHEN** downstream MCP client configuration is rendered
- **THEN** clients SHALL receive MCPHub all, enabled group, enabled server, and disabled smart endpoints instead of direct per-server process entries
- **AND** registries without `mcphub` SHALL continue to render direct per-server entries.
