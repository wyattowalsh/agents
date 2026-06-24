# mcp-audit Specification

## Purpose
Define MCP audit requirements for server conformance, transport, auth, secrets handling, sandboxing, and skill replacement fit.
## Requirements
### Requirement: MCP live-system justification

The MCP audit lane SHALL keep MCP servers only when live or dynamic external state is required and SHALL record transport, auth, secrets, sandbox, and smoke fixture requirements.

#### Scenario: MCPHub exposes ChatGPT remote access through an opt-in tunnel

- **GIVEN** ChatGPT requires a remote HTTPS MCP URL
- **WHEN** MCPHub tunnel exposure is enabled
- **THEN** MCPHub SHALL remain bound to localhost
- **AND** the tunnel sidecar SHALL use local-only Cloudflare credentials or tokens
- **AND** tracked files SHALL not contain real tunnel credentials, bearer tokens, or Zapier webhook URLs.

