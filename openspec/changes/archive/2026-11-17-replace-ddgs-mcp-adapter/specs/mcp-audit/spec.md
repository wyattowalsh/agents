# mcp-audit Delta

## ADDED Requirements

### Requirement: DDGS uses upstream MCP server

The MCP registry SHALL launch DDGS through the upstream `ddgs[mcp]` package entry point so managed harnesses receive the upstream DDGS MCP tool surface.

#### Scenario: DDGS launches through upstream CLI

- **GIVEN** MCPHub renders the `ddgs` server from `config/mcp-registry.json`
- **WHEN** the server process starts
- **THEN** the command SHALL be `uvx`
- **AND** the args SHALL be `["--from", "ddgs[mcp]", "ddgs", "mcp"]`
- **AND** the server SHALL keep `auth_policy: none`.

#### Scenario: Existing DDGS endpoint remains stable

- **GIVEN** harnesses consume DDGS through MCPHub groups
- **WHEN** registry and MCPHub settings are regenerated
- **THEN** the MCPHub server id SHALL remain `ddgs`
- **AND** the server SHALL remain excluded from the public `tunnel` group.
- **AND** no MCPHub group SHALL use the id `ddgs` and shadow the direct server endpoint.

#### Scenario: MCPHub completes the negotiated request lifecycle

- **GIVEN** the all, direct DDGS, or harness MCPHub route is under smoke test
- **WHEN** the client initializes a session
- **THEN** it SHALL validate the final response headers and matching JSON-RPC initialize result
- **AND** it SHALL require a non-empty session id and negotiated protocol version
- **AND** it SHALL send `notifications/initialized` and require HTTP 202
- **AND** it SHALL reuse the session id and negotiated protocol version for `tools/list`.

#### Scenario: Direct DDGS route exposes the exact upstream tool surface

- **GIVEN** the upstream DDGS MCP server is running under MCPHub
- **WHEN** an MCP client lists tools through `/mcp/ddgs`
- **THEN** the listed names SHALL equal `ddgs-search_text`, `ddgs-search_images`, `ddgs-search_news`, `ddgs-search_videos`, `ddgs-search_books`, and `ddgs-extract_content` without duplicates or pagination.

#### Scenario: Harness group contains the upstream DDGS tool surface

- **GIVEN** the upstream DDGS MCP server is running under MCPHub
- **WHEN** an MCP client lists tools through `/mcp/harness`
- **THEN** the harness-group listed tools SHALL include `ddgs-search_text`, `ddgs-search_images`, `ddgs-search_news`, `ddgs-search_videos`, `ddgs-search_books`, and `ddgs-extract_content`.

#### Scenario: JSON and SSE response forms are validated hermetically

- **GIVEN** MCPHub may return `application/json` or `text/event-stream`
- **WHEN** the smoke helper parses initialize or tools/list output
- **THEN** it SHALL select the matching JSON-RPC response id and reject errors or malformed result shapes
- **AND** it SHALL handle UTF-8 BOMs, CRLF and CR line endings, comments, empty SSE events, joined data fields, and a final event without a blank terminator
- **AND** it SHALL reject non-string or duplicate tool names and any non-empty `nextCursor`.
