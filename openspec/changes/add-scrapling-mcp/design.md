# Design

## Approach

Add `scrapling` directly to `config/mcp-registry.json` using the same registry schema as existing uvx-managed stdio MCP servers. Launch through a repo wrapper script that pins `scrapling[ai]==0.4.10` before `uvx scrapling mcp`.

Keep the server enabled globally but exclude it from default client profiles (`harness`, `tunnel`). Expose through opt-in capability and workflow groups only.

## Data And Control Flow

1. `config/mcp-registry.json` defines `scrapling` and group memberships.
2. `scripts/generate_mcphub_settings.py` emits `mcp/mcphub/mcp_settings.json`.
3. `scripts/sync_agent_stack.py` renders repo MCP outputs from the registry.

## Integration Points

- `scrapling`:
  - `transport`: `stdio`
  - `command`: `bash`
  - `args`: `["${REPO_ROOT}/scripts/mcphub/scrapling-stdio.sh"]`
- Wrapper launches:
  - `uvx --from scrapling[ai]==0.4.10 scrapling mcp`
  - User overrides via `.env.mcphub` using `MCPHUB_SCRAPLING_PACKAGE` or `SCRAPLING_EXECUTABLE_PATH` (not committed)

## Group Membership

| Group | Shape |
|-------|-------|
| `web-read` | `get`, `bulk_get` only |
| `shared-read` | `get` only |
| `research` | full server |
| `media-work` | full server |
| `live-browser` | full server |
| `heavy` | full server |
| `experimental` | full server |
| `harness`, `tunnel`, `browser` | excluded |

## Alternatives Rejected

- Direct `scrapling` in registry without wrapper: rejected because version pin and env forwarding belong in fleet wrapper.
- Default `harness` membership: rejected; browser spawn and large payloads violate bounded default policy.
- `scrapling mcp --http`: rejected; MCPHub stdio child model does not use Streamable HTTP for this server.
- Docker `pyd4vinci/scrapling` launch: deferred maintainer path; uvx matches repo Python conventions.

## Migration Or Compatibility Notes

No compatibility shim needed. Existing unmanaged user MCP servers are preserved by merge logic in sync.