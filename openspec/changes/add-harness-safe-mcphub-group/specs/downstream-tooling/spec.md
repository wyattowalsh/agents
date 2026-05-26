# Downstream Tooling Delta

## MODIFIED Requirements

### Requirement: MCPHub endpoint projection is source-traceable

Generated downstream tool artifacts SHALL be derived from canonical repo sources and SHALL document their owning source file or command.

#### Scenario: Harnesses receive the safe MCPHub group endpoint

- **GIVEN** `mcphub.enabled` is true in the MCP registry
- **AND** the `harness-safe` MCPHub group is enabled
- **WHEN** managed harness MCP configuration is rendered and merged
- **THEN** each harness SHALL receive the enabled MCPHub entry named `mcphub_group_harness-safe`
- **AND** that entry SHALL point to the `/mcp/harness-safe` endpoint
- **AND** each enabled repository MCP server SHALL be projected as an individual disabled MCPHub server endpoint
- **AND** no individual server endpoint SHALL be enabled by default
- **AND** stale MCPHub all, group, server, or smart entries SHALL be removed from merged harness outputs where the sync owns cleanup
- **AND** bearer auth SHALL use an environment or file placeholder rather than a literal token.
