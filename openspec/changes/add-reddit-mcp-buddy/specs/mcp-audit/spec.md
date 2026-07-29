# mcp-audit Delta

## ADDED Requirements

### Requirement: Reddit MCP remains anonymous-first and opt-in

The MCP registry SHALL register `reddit-mcp-buddy` as an enabled stdio server launched through the repo-managed pinned wrapper, while keeping the server outside default and remotely exposed MCPHub groups.

#### Scenario: Reddit MCP launches through the pinned fleet wrapper

- **GIVEN** MCPHub renders `reddit-mcp-buddy` from `config/mcp-registry.json`
- **WHEN** the server process starts
- **THEN** the launch command SHALL be `bash ${REPO_ROOT}/scripts/mcphub/reddit-mcp-buddy-stdio.sh`
- **AND** the wrapper SHALL launch the audited `reddit-mcp-buddy@1.1.13` package unless a user-owned local version override is present
- **AND** tracked registry configuration SHALL not contain Reddit credentials.

#### Scenario: Reddit MCP exposure is explicitly opt-in

- **GIVEN** managed harness clients default to the `harness` group
- **WHEN** registry and MCPHub settings are generated
- **THEN** `reddit-mcp-buddy` SHALL be absent from `harness` and `tunnel`
- **AND** it SHALL be available only through the `research`, `shared-read`, and `experimental` groups
- **AND** those groups SHALL expose the audited five-tool read-only surface without write or posting tools.

#### Scenario: Reddit content and optional credentials preserve trust boundaries

- **GIVEN** an agent invokes Reddit MCP tools
- **WHEN** Reddit posts, comments, or user data are returned
- **THEN** the content SHALL be treated as untrusted external evidence
- **AND** anonymous access SHALL remain the safe default
- **AND** optional `REDDIT_*` credentials SHALL remain user-owned in `.env.mcphub` and SHALL never be committed.
