# mcp-audit Delta

## ADDED Requirements

### Requirement: Package version check MCP replacement

The MCP registry SHALL replace the legacy `package-version` server with `package-version-check-mcp`, launched through `scripts/mcphub/package-version-check-mcp.sh`, while preserving bounded package-version lookup access for managed harness and research groups.

#### Scenario: Package version check launches through repo wrapper

- **GIVEN** MCPHub renders package-version lookup tools from `config/mcp-registry.json`
- **WHEN** the server process starts
- **THEN** the launch command SHALL be `bash ${REPO_ROOT}/scripts/mcphub/package-version-check-mcp.sh`
- **AND** the wrapper SHALL invoke the upstream PyPI package through `uvx`
- **AND** optional GitHub rate-limit credentials SHALL remain user-owned environment values rather than tracked secrets.

#### Scenario: Package version groups use the replacement slug

- **GIVEN** managed MCPHub groups include package-version lookup capability
- **WHEN** registry and downstream harness projections are generated
- **THEN** those projections SHALL use the `package-version-check-mcp` server slug
- **AND** default bounded groups SHALL expose the replacement tools without restoring the deprecated endpoint as an active server.

#### Scenario: Legacy package-version residue is limited to removal accounting

- **GIVEN** maintainers search tracked source for the legacy `package-version` server slug
- **WHEN** the replacement is complete
- **THEN** remaining legacy references SHALL be limited to explicit removal, migration, or audit notes
- **AND** no active registry entry or generated MCPHub server config SHALL launch the legacy Go implementation.
