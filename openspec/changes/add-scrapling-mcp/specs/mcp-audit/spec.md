# mcp-audit Delta

## ADDED Requirements

### Requirement: Scrapling MCP opt-in registry integration

The MCP registry SHALL register `scrapling` as an enabled stdio MCP server launched through `scripts/mcphub/scrapling-stdio.sh` with a pinned `scrapling[ai]` package, and SHALL expose it only through opt-in MCPHub groups while excluding default `harness`, `tunnel`, and capability `browser` profiles.

#### Scenario: Scrapling launches through fleet wrapper

- **GIVEN** MCPHub renders `scrapling` from `config/mcp-registry.json`
- **WHEN** the server process starts
- **THEN** the launch command SHALL be `bash ${REPO_ROOT}/scripts/mcphub/scrapling-stdio.sh`
- **AND** the wrapper SHALL exec `uvx --from scrapling[ai]==<pinned> scrapling mcp`
- **AND** tracked config SHALL not contain proxy secrets or custom browser paths.

#### Scenario: Scrapling group membership is bounded by default exposure

- **GIVEN** managed harness clients default to the `harness` group
- **WHEN** `scrapling` is added to the registry
- **THEN** `scrapling` SHALL be absent from `harness`, `tunnel`, and `browser` groups
- **AND** `scrapling` SHALL be present in `research`, `media-work`, `live-browser`, `heavy`, and `experimental` as a full server
- **AND** `web-read` SHALL expose only `get` and `bulk_get`
- **AND** `shared-read` SHALL expose only `get`.

#### Scenario: Scrapling scraped content is untrusted evidence

- **GIVEN** an agent invokes Scrapling MCP tools
- **WHEN** page content is returned to the model
- **THEN** maintainers SHALL document scraped content as untrusted external evidence
- **AND** proxy and `SCRAPLING_EXECUTABLE_PATH` overrides SHALL remain user-owned in `.env.mcphub` only
- **AND** persistent browser sessions SHALL be closed with `close_session` to avoid resource leaks.