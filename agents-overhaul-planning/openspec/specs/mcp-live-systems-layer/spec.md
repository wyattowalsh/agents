# mcp-live-systems-layer

## Requirements

### Requirement: Mcp Live Systems Layer

The system SHALL only promote MCP servers when live external state or protocol-specific behavior is required and SHALL classify transport, auth, sandbox, and security risks.

#### Scenario: validation

- **Given** the canonical manifests and latest repo inventory
- **When** the relevant validation command runs
- **Then** generated docs/config/test fixtures match the manifests or the command fails with actionable remediation.
