# Downstream Tooling Delta

## ADDED Requirements

### Requirement: ChatGPT remote MCP handoff is stable and source-traceable

ChatGPT remote MCP access SHALL use the MCPHub public URL declared in local
MCPHub environment configuration and documented by repo-owned MCPHub docs.

#### Scenario: MCPHub tunnel reports the public URL

- **GIVEN** `MCPHUB_TUNNEL_ENABLED=true`
- **AND** `MCPHUB_PUBLIC_URL` is set
- **WHEN** MCPHub starts and passes its health check
- **THEN** the tunnel sidecar SHALL expose the same public `/mcp` URL for ChatGPT
- **AND** optional Zapier handoff SHALL report that public URL without including bearer tokens.
