# Design

## Approach

Register `ddgs` in `config/mcp-registry.json` as an enabled stdio MCP server launched with `uvx ddgs-mcp-server==0.5.1` and `auth_policy: none`. Add alongside `duckduckgo-search` in workflow groups including default `harness`; exclude from `tunnel`.

## Data And Control Flow

1. `config/mcp-registry.json` defines `ddgs` and group memberships.
2. `scripts/generate_mcphub_settings.py` emits `mcp/mcphub/mcp_settings.json`.
3. `scripts/sync_agent_stack.py` renders repo MCP client projections from the registry.

## Integration Points

- `ddgs`:
  - `transport`: `stdio`
  - `command`: `uvx`
  - `args`: `["ddgs-mcp-server==0.5.1"]`
- Tools: `search_text`, `search_news` (optional `fetch_full_content` on `search_text`)

## Group Membership

| Group | Shape |
|-------|-------|
| `harness`, `daily`, `coding`, `research`, `review`, `web-search`, `shared-read` | full server after `duckduckgo-search` |
| `tunnel`, `credentialed`, `experimental` | excluded |

## Operator Guidance

- Prefer DDGS snippet search; avoid `fetch_full_content` unless bounded research (large payloads, +latency).
- Coexist with `duckduckgo-search`; do not replace it.

## Alternatives Rejected

- Replacing `duckduckgo-search`: rejected; maintain complementary surfaces.
- `tunnel` membership: rejected; keep remote ChatGPT surface minimal.
- Wrapper script for pin: deferred; args pin is sufficient for audited 0.5.1.

## Migration Or Compatibility Notes

No compatibility shim. Registry merge logic preserves user-owned MCP overrides on sync.