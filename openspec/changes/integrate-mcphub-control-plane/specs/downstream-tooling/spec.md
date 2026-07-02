# Downstream Tooling Delta

## ADDED Requirements

### Requirement: MCPHub endpoint projection is source-traceable

Generated downstream tool artifacts SHALL be derived from canonical repo sources and SHALL document their owning source file or command.

#### Scenario: MCPHub client endpoints are projected

- **GIVEN** `mcphub.enabled` is true in the MCP registry
- **WHEN** downstream MCP client configuration is rendered
- **THEN** managed harness clients SHALL receive the enabled MCPHub `harness` group endpoint plus disabled individual server endpoints instead of direct per-server process entries
- **AND** ChatGPT SHALL receive only the bounded MCPHub `tunnel` group endpoint from the public MCPHub URL
- **AND** Cherry Studio import packs MAY include all, group, server, and smart endpoint files for explicit manual import
- **AND** registries without `mcphub` SHALL continue to render direct per-server entries.
