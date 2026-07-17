# Design

## Approach

Add `reddit-mcp-buddy` directly to `config/mcp-registry.json` using the same registry schema as existing npx-managed stdio MCP servers. Launch through a repo wrapper that pins `reddit-mcp-buddy@1.1.13` and loads optional local secrets via `mcphub_load_env`.

Keep the server enabled globally but exclude it from default client profiles (`harness`, `tunnel`). Expose through opt-in workflow/risk groups only.

## Data And Control Flow

1. `config/mcp-registry.json` defines `reddit-mcp-buddy` and group memberships.
2. `scripts/generate_mcphub_settings.py` emits `mcp/mcphub/mcp_settings.json` (servers sorted alphabetically).
3. `scripts/sync_agent_stack.py` renders repo MCP projections from the registry.
4. Wrapper loads `.env.mcphub` and execs pinned `npx`.

## Integration Points

- `reddit-mcp-buddy`:
  - `transport`: `stdio`
  - `command`: `bash`
  - `args`: `["${REPO_ROOT}/scripts/mcphub/reddit-mcp-buddy-stdio.sh"]`
  - `env`: `{}` (no tracked secrets; optional REDDIT_* only in local `.env.mcphub`)
- Wrapper:
  - `npx -y reddit-mcp-buddy@${MCPHUB_REDDIT_MCP_BUDDY_VERSION:-1.1.13}`
  - No `--http`, no `--auth`

## Group Membership

| Group | Shape |
|-------|-------|
| `research` | full server |
| `shared-read` | full server |
| `experimental` | full server |
| `harness`, `tunnel` | excluded |
| `web-search`, `web-read`, `credentialed` | excluded |

## Local Credential Audit

Machine audit found no existing `REDDIT_*` env vars, no `.env.mcphub` Reddit keys, no `~/.reddit-mcp-buddy` auth store, and no harness MCP reddit entries. Anonymous mode is the only path that works without new secrets.

## Capability Mapper Bypass

Manual mapping is sufficient: single third-party package, documented read-only tools, same fleet pattern as scrapling/open-websearch. No multi-tool capability matrix ambiguity requiring `mcp-capability-mapper`.

## Alternatives Rejected

- Direct `npx` in registry without wrapper: rejected; pin + env load belong in fleet wrapper.
- Registry env placeholders for `REDDIT_PASSWORD`: rejected; would surface password keys in generated settings; wrapper + local env is enough.
- Default `harness` membership: rejected; keeps schema/context tax bounded.
- Skills catalog MDX: rejected; upstream has no SKILL.md.
- New `social` capability group: rejected; existing research/shared-read/experimental cover opt-in.

## Migration Or Compatibility Notes

No compatibility shim. Existing unmanaged user MCP servers are preserved by merge logic in sync.
