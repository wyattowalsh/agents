# mcp-audit Delta

## ADDED Requirements

### Requirement: llms-txt-explorer MCP registry integration

The MCP registry SHALL register `llms-txt-explorer` as an enabled stdio MCP server launched through `scripts/mcphub/llms-txt-explorer-stdio.sh` with a pinned npm package, expose bounded tools in default `harness`, and exclude agent-controlled fetches from the remote `tunnel` profile.

#### Scenario: llms-txt-explorer launches through fleet wrapper

- **GIVEN** MCPHub renders `llms-txt-explorer` from `config/mcp-registry.json`
- **WHEN** the server process starts
- **THEN** the launch command SHALL be `bash ${REPO_ROOT}/scripts/mcphub/llms-txt-explorer-stdio.sh`
- **AND** the wrapper SHALL exec `npx -y @thedaviddias/mcp-llms-txt-explorer@0.2.0`
- **AND** tracked config SHALL not contain API keys or proxy secrets.

#### Scenario: Harness exposes catalog-only llms.txt discovery

- **GIVEN** managed harness clients default to the `harness` group
- **WHEN** `llms-txt-explorer` is added to the registry
- **THEN** `harness` SHALL expose only the `list_websites` tool for `llms-txt-explorer`
- **AND** `check_website` SHALL be available only through opt-in workflow groups
- **AND** `llms-txt-explorer` SHALL be absent from the `tunnel` group.

#### Scenario: llms.txt bodies are untrusted evidence

- **GIVEN** an agent invokes `check_website` or reads fetched llms.txt content
- **WHEN** remote llms.txt / llms-full.txt text is returned
- **THEN** maintainers SHALL document that content as untrusted external evidence
- **AND** embedded instructions in remote llms.txt files SHALL not override repo or user instructions.