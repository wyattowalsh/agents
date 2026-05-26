# mcp-audit Delta

## MODIFIED Requirements

### Requirement: MCP live-system justification

The MCP audit lane SHALL keep MCP servers only when live or dynamic external state is required and SHALL record transport, auth, secrets, sandbox, and smoke fixture requirements.

#### Scenario: MCPHub startup repairs stale local process state

- **GIVEN** MCPHub is the local control plane for managed MCP clients
- **WHEN** the pid file exists but `/health` fails
- **THEN** startup SHALL not treat pid existence alone as healthy state
- **AND** managed wrapper and child processes MAY be stopped only after command-line ownership is verified
- **AND** arbitrary unrelated PIDs SHALL NOT be killed
- **AND** doctor output SHALL distinguish health, listener, wrapper pid, child pid, and stale-or-wedged state.
