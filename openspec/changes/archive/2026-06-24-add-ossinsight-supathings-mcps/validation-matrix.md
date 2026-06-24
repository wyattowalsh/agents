# Validation Matrix

| Surface | Command | Expected Result | Notes |
|---------|---------|-----------------|-------|
| OpenSpec artifacts | `uv run wagents openspec validate` | Change artifacts validate | Run after creating and after completing tasks. |
| Registry and repo outputs | `uv run python scripts/sync_agent_stack.py --targets repo --apply` | Repo MCP/config surfaces regenerate from registry | Must not manually edit generated repo surfaces. |
| Home/global outputs | `uv run python scripts/sync_agent_stack.py --targets home --apply` | Managed home harness configs receive both servers | Preserves user-owned unknown MCP servers. |
| Docs | `uv run wagents docs generate` | Generated docs refresh without errors | Run after KB/doc source edits. |
| Sync drift | `uv run python scripts/sync_agent_stack.py --targets repo,home --check` | No generated drift remains | May fail only for unrelated pre-existing dirty files; capture output. |
| Asset validation | `uv run wagents validate` | Skills, agents, and configs validate | Standard repo validation. |
| Package launch probes | `npx -y ossinsight-mcp --help` and `npx -y supathings-mcp --help` | Packages resolve and print help or startup info | SupaThings may require macOS/Things 3 for full runtime behavior. |

## Blockers

- None known.

## Deferred Checks

- Full SupaThings runtime task access depends on local Things 3 installation and macOS automation permissions.
- Full OSSInsight runtime behavior depends on upstream public API availability and rate limits.
