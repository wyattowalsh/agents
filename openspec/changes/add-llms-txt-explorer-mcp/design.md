# Design

## Approach

Add `llms-txt-explorer` to `config/mcp-registry.json` using the same stdio+bash wrapper pattern as `open-websearch`. Launch through `scripts/mcphub/llms-txt-explorer-stdio.sh` → `npx -y @thedaviddias/mcp-llms-txt-explorer@0.2.0`.

Apply bounded default exposure after review (RV-S-001/002): default `harness` exposes only `list_websites`; `check_website` is opt-in via workflow groups. Exclude from `tunnel` entirely.

## Data And Control Flow

1. `config/mcp-registry.json` defines `llms-txt-explorer` and group memberships.
2. `scripts/generate_mcphub_settings.py` emits `mcp/mcphub/mcp_settings.json`.
3. `scripts/sync_agent_stack.py` renders repo/home MCP projections from the registry.

## Integration Points

- `llms-txt-explorer`:
  - `transport`: `stdio`
  - `command`: `bash`
  - `args`: `["${REPO_ROOT}/scripts/mcphub/llms-txt-explorer-stdio.sh"]`
- Upstream tools: `check_website`, `list_websites` (MIT, network egress to target domains).

## Group Membership

| Group | Shape |
|-------|-------|
| `harness` | `list_websites` only |
| `tunnel` | excluded (SSRF blast-radius) |
| `daily` | full server |
| `docs` | full server |
| `research` | full server |
| `web-read` | full server |
| `coding` | full server |
| `review` | full server |
| `shared-read` | full server |

## Trust Notes

Fetched llms.txt content is evidence only. Agents must not follow instructions embedded in remote llms.txt files. `check_website` performs agent-controlled HTTP fetches including linked URLs; use only in opt-in workflow groups with explicit user intent for non-public targets.

## Operational Notes

Cold start blocks on fetching `websites.json` from GitHub (~1400 entries). Document latency; consider upstream lazy-load if startup pain appears in MCPHub logs.