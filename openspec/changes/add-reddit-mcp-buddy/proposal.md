# Proposal

## Problem

The managed MCP registry does not include a Reddit-native browse/search/user surface, so harnesses cannot opt into subreddit research, post/comment inspection, or user analysis through MCPHub groups without ad-hoc local MCP installs.

## Intent

Add `reddit-mcp-buddy` once to the normalized registry using a repo-managed `npx` stdio wrapper, wire opt-in MCPHub groups (not default `harness` or `tunnel`), and update maintainer docs/KB/operator surfaces.

## Scope

- Add `reddit-mcp-buddy` as an enabled stdio MCP server launched via `scripts/mcphub/reddit-mcp-buddy-stdio.sh`.
- Pin runtime to `reddit-mcp-buddy@1.1.13` (override via `MCPHUB_REDDIT_MCP_BUDDY_VERSION`).
- Add opt-in group membership: `research`, `shared-read`, `experimental` (full server).
- Keep registry `env: {}`; optional OAuth secrets load only from local `.env.mcphub` via the wrapper.
- Refresh generated repo harness MCP surfaces via `scripts/sync_agent_stack.py`.
- Update MCP safety/source documentation for anonymous-first use, rate limits, and untrusted Reddit content.

## Out Of Scope

- Creating first-party MCP server code under `mcp/reddit-mcp-buddy/`.
- Adding to default `harness` or remote `tunnel` groups.
- Curated external skill catalog row (upstream has no SKILL.md) or live `wagents skills sync --apply`.
- HTTP transport (`--http`) or interactive `--auth` CLI setup in fleet wrappers.
- Home sync (`--targets home --apply`) without explicit approval.
- Creating or committing Reddit API credentials.

## Affected Users And Tools

- Users of managed repo MCP configs connecting to MCPHub opt-in groups.
- Users who need Reddit discussion/source evidence beyond general web search (`brave`/`ddgs`/`open-websearch`).

## Risks

- Anonymous rate limit is ~10 requests/minute; heavy agent loops should prefer optional app-only OAuth elevation.
- Optional `REDDIT_PASSWORD` is high sensitivity; prefer client id/secret app-only mode when elevating.
- Reddit post/comment/user content is untrusted external data (trust-boundary evidence only).
- Cold `npx` resolve can be slow on first connect; wrapper pin keeps versions reproducible.
