# Design

## Approach

Add `open-websearch` directly to `config/mcp-registry.json` using the same registry schema as existing npx-managed stdio MCP servers. Launch through a repo wrapper script that forces fleet-safe environment defaults before `npx -y open-websearch@latest`.

Keep the server enabled globally but exclude it from default client profiles (`harness`, `tunnel`). Expose through opt-in capability and workflow groups only.

## Data And Control Flow

1. `config/mcp-registry.json` defines `open-websearch` and group memberships.
2. `scripts/generate_mcphub_settings.py` emits `mcp/mcphub/mcp_settings.json`.
3. `scripts/sync_agent_stack.py` renders repo MCP outputs from the registry.
4. Curated skill catalog row lives in `docs/src/authoring/skills/open-websearch.mdx`; Skills CLI sync is dry-run only unless explicitly requested.

## Integration Points

- `open-websearch`:
  - `transport`: `stdio`
  - `command`: `bash`
  - `args`: `["${REPO_ROOT}/scripts/mcphub/open-websearch-stdio.sh"]`
- Wrapper exports:
  - `MODE=stdio`
  - `DEFAULT_SEARCH_ENGINE=duckduckgo`
  - `SEARCH_MODE=request`
  - `ALLOWED_SEARCH_ENGINES=duckduckgo,startpage,bing,brave`
  - User overrides via `.env.mcphub` using `OPEN_WEBSEARCH_*` prefixes (not committed)

## Group Membership

| Group | Shape |
|-------|-------|
| `web-search` | full server |
| `research` | full server |
| `experimental` | full server |
| `web-read` | `fetchWebContent`, `fetchGithubReadme` only |
| `shared-read` | `search`, `fetchWebContent` only |
| `harness`, `tunnel` | excluded |

## Alternatives Rejected

- Direct `npx` in registry without wrapper: rejected because upstream default `MODE=both` starts HTTP+stdio and `SEARCH_MODE=auto` can pull Playwright.
- Default `harness` membership: rejected per maintainer choice; bounded default already includes brave + duckduckgo + ddgs.
- Vendor copy into `skills/`: rejected per AGENTS.md §2.7 curated external policy.

## Migration Or Compatibility Notes

No compatibility shim is needed. Existing unmanaged user MCP servers are preserved by merge logic in sync.