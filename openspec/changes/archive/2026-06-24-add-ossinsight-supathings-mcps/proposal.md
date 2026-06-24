# Proposal

## Problem

The managed MCP registry does not include OSSInsight or SupaThings, so repo and home harness configs cannot expose GitHub ecosystem analytics or Things 3 task automation consistently across supported tools.

This affects canonical MCP configuration and generated downstream harness surfaces, so the change needs OpenSpec tracking instead of a direct trivial edit.

## Intent

Add both MCP servers once to the normalized registry using package-manager launches preferred by the user, then regenerate repo and home harness configs from that source.

## Scope

- Add `ossinsight` as an enabled stdio MCP server launched with `npx -y ossinsight-mcp`.
- Add `supathings` as an enabled stdio MCP server launched with `npx -y supathings-mcp`.
- Refresh generated repo and home harness MCP surfaces via `scripts/sync_agent_stack.py`.
- Update MCP safety/source documentation for public API limits and local Things 3 access.

## Out Of Scope

- Creating first-party MCP server code under `mcp/<name>/`.
- Adding local checkout/build management to `scripts/mcp_tools/check_installed_mcps.sh` or `update_installed_mcps.sh`.
- Adding secrets, env values, or harness-specific tool approvals.
- Changing MCP/plugin ownership rules for Chrome DevTools or other existing servers.

## Affected Users And Tools

- Users of managed repo and global MCP configs for Claude Desktop, ChatGPT, Codex, GitHub Copilot CLI, Cursor, Gemini CLI, Antigravity, OpenCode, Perplexity Desktop, Cherry Studio, and related generated surfaces.
- Users with Things 3 installed on macOS who want task access through SupaThings.
- Users who rely on OSSInsight public API access for GitHub analytics.

## Generated Surfaces To Refresh

- `mcp.json`
- `.vscode/mcp.json`
- `opencode.json`
- repo-generated instruction/hook surfaces produced by `scripts/sync_agent_stack.py --targets repo --apply`
- home/global harness config surfaces produced by `scripts/sync_agent_stack.py --targets home --apply`
- generated docs pages produced by `uv run wagents docs generate`

## Risks

- `ossinsight` uses a public API with upstream documented rate limits, so high-volume use may throttle by IP. The upstream repo README currently lists a stale scoped npm package, so the registry uses the published `ossinsight-mcp` package verified through npm.
- `supathings` accesses local Things 3 data and may write/update tasks through local macOS automation, so users should treat it as a local data-access MCP.
- Home sync may touch user-level config files outside the repo; it must be performed through the canonical sync script rather than manual edits.
