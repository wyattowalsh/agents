# Design

## Approach

Add both servers directly to `config/mcp-registry.json` using the same registry schema and defaults as existing npx-managed stdio MCP servers. Keep them enabled globally, with no env vars, no tool restrictions, no platform overrides, and standard startup/operation timeouts.

## Data And Control Flow

1. `config/mcp-registry.json` defines `ossinsight` and `supathings` as normalized MCP entries.
2. `scripts/sync_agent_stack.py` renders repo MCP outputs and OpenCode config from the registry for repo targets.
3. The same sync script merges managed entries into home/global harness configs while preserving unknown user servers.
4. Docs and KB pages record provenance and safety notes for future audits.

## Integration Points

- `ossinsight`:
  - `transport`: `stdio`
  - `command`: `npx`
  - `args`: `[-y, ossinsight-mcp]`
- `supathings`:
  - `transport`: `stdio`
  - `command`: `npx`
  - `args`: `[-y, supathings-mcp]`

Both entries use:

- `env`: `{}`
- `enabled`: `true`
- `startup_timeout_sec`: `90`
- `timeout_ms`: `600000`
- `tools`: `[*]`
- `tool_approvals`: `{}`
- `platform_overrides`: `{}`

## Alternatives Rejected

- Local checkout/build integration under `mcp/servers`: rejected because both selected launch paths resolve through npx and the user prefers npx/uvx.
- The OSSInsight README's scoped package name: rejected because npm returns 404 for `@modelcontextprotocol/server-ossinsight`; `ossinsight-mcp` is the published package that resolves with `npx`.
- Harness-specific manual edits: rejected because `config/mcp-registry.json` is the canonical source and generated/home surfaces must be synced.
- Tool approval overrides: rejected because the current registry convention leaves approvals empty unless there is a concrete harness-specific requirement.

## Migration Or Compatibility Notes

No compatibility shim is needed. These are new registry entries and generated downstream surfaces can be updated from the canonical source. Existing unmanaged user MCP servers should be preserved by merge logic.
