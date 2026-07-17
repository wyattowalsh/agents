# MCP Audit Spec Delta — qsv + data group

## ADDED Requirements

### Requirement: Tabular data capability group
MCPHub SHALL expose a managed capability group named `data` for local tabular data wrangling servers.

#### Scenario: data group includes qsv
- **GIVEN** the MCP registry includes server `qsv`
- **WHEN** MCPHub settings are generated
- **THEN** group `data` SHALL list `qsv`
- **AND** `qsv` SHALL NOT appear in `harness` or `tunnel`

### Requirement: qsv MCP server registration
The registry SHALL register `qsv` as a stdio MCP server launched via the repo wrapper `scripts/mcphub/qsv-stdio.sh` with explicit `tools_allow_all: true` when using wildcard tools.

#### Scenario: wrapper-based stdio launch
- **GIVEN** a local build exists at `mcp/servers/qsv-agent-skills/dist/mcp-server.js`
- **AND** `qsv` or `qsvmcp` is on PATH (or `QSV_MCP_BIN_PATH` is set)
- **WHEN** MCPHub starts the `qsv` server
- **THEN** the wrapper SHALL resolve the binary and execute the Node MCP server over stdio
