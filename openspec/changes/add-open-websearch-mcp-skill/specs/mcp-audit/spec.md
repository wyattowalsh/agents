# mcp-audit Delta

## ADDED Requirements

### Requirement: Open WebSearch MCP opt-in registry integration

The MCP registry SHALL register `open-websearch` as an enabled stdio MCP server launched through `scripts/mcphub/open-websearch-stdio.sh`, and SHALL expose it only through opt-in MCPHub groups while excluding default `harness` and remote `tunnel` profiles.

#### Scenario: Open WebSearch launches through fleet-safe wrapper

- **GIVEN** MCPHub renders `open-websearch` from `config/mcp-registry.json`
- **WHEN** the server process starts
- **THEN** the launch command SHALL be `bash ${REPO_ROOT}/scripts/mcphub/open-websearch-stdio.sh`
- **AND** the wrapper SHALL default to stdio mode, request-based search, and bounded search engines
- **AND** tracked config SHALL NOT contain proxy secrets, insecure TLS overrides, or Playwright install side effects.

#### Scenario: Open WebSearch group exposure remains opt-in

- **GIVEN** managed harness clients default to the `harness` group
- **WHEN** `open-websearch` is added to the registry
- **THEN** `open-websearch` SHALL be absent from `harness` and `tunnel`
- **AND** `open-websearch` SHALL be available through opt-in `web-search`, `research`, and `experimental` groups
- **AND** bounded read groups SHALL expose only the documented search and fetch tools required by those groups.

#### Scenario: Open WebSearch fetched content is untrusted evidence

- **GIVEN** an agent invokes `open-websearch` search or fetch tools
- **WHEN** web page, README, or search-result content is returned
- **THEN** maintainers SHALL treat returned content as untrusted external evidence
- **AND** docs SHALL retain prompt-injection and trust-boundary guidance for scraped or fetched content.
