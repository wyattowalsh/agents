# Design

## Approach

Use the upstream DDGS package's built-in MCP entry point instead of the wrapper package:

```json
{
  "command": "uvx",
  "args": ["--from", "ddgs[mcp]", "ddgs", "mcp"]
}
```

This keeps dependency resolution fresh while matching the upstream documented client configuration shape. The server slug remains `ddgs`, so existing MCPHub group membership and client endpoint naming do not change.

## Runtime Contract

- Transport: stdio.
- Authentication: none.
- Launch owner: MCPHub via the generated `mcp/mcphub/mcp_settings.json`.
- Expected tools from upstream DDGS MCP: `search_text`, `search_images`, `search_news`, `search_videos`, `search_books`, `extract_content`.

## Data And Control Flow

1. `config/mcp-registry.json` defines the `ddgs` launch command.
2. `scripts/generate_mcphub_settings.py` renders `mcp/mcphub/mcp_settings.json`.
3. `wagents docs compose --regen-configs --config mcp-registry` embeds the registry in public docs.
4. `scripts/mcphub/smoke.sh` initializes the all, direct DDGS, and harness routes, sends `notifications/initialized`, and reuses the negotiated protocol version and session id for `tools/list`.
5. `scripts/mcphub/mcp_response.py` validates the final HTTP response block and decodes either JSON or SSE without logging the response body or bearer token.
6. Runtime smoke requires the direct DDGS route to expose exactly the six expected prefixed tools and the harness route to contain all six.

## Runtime Assurance

- Every route completes the Streamable HTTP lifecycle: `initialize`, `notifications/initialized`, then `tools/list`.
- The initialize response must include a non-empty `result.protocolVersion` and final `MCP-Session-Id` header. Both values are reused on subsequent requests.
- The initialized notification must return HTTP 202.
- Response parsing uses the final HTTP header block, supports `application/json` and `text/event-stream`, and matches the requested JSON-RPC response id.
- SSE handling accepts UTF-8 BOMs, CRLF or CR line endings, comments, empty events, multiple `data` fields, and a final event without a trailing blank line.
- Tool-list validation rejects JSON-RPC errors, malformed tool entries, duplicate names, and non-empty pagination cursors.
- Curl requests use bounded connect and total timeouts. Failure output never includes bearer credentials or response bodies.

## Compatibility

The MCPHub server id remains `ddgs`, so configured group memberships and the stable direct endpoint continue to use `/mcp/ddgs`. No group may use the `ddgs` id because that would shadow the direct server route. The tool surface expands; existing `search_text` and `search_news` callers keep their prefixed MCPHub tool names.

## Risks

- Unpinned `ddgs[mcp]` follows the latest PyPI release and can drift. This is intentional for current dependency posture but should be watched by runtime smoke tests.
- `extract_content` can fetch arbitrary URLs and return large payloads. Operator docs should prefer snippet search and reserve extraction for bounded research.
- Image/video/book result schemas vary by upstream backend.
- The exact direct-route assertion deliberately fails when upstream adds or removes tools, forcing an explicit contract review. The harness assertion is containment-based because that route aggregates multiple servers.
