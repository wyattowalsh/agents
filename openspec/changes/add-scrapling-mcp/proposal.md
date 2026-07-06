# Proposal

## Problem

The managed MCP registry does not include Scrapling, so harnesses cannot opt into CSS-targeted web scraping, anti-bot fetch, or browser-session extraction through MCPHub groups.

## Intent

Add `scrapling` once to the normalized registry using a repo-managed `uvx` stdio wrapper, wire opt-in MCPHub groups (not default `harness` or `tunnel`), and update maintainer docs/KB surfaces.

## Scope

- Add `scrapling` as an enabled stdio MCP server launched via `scripts/mcphub/scrapling-stdio.sh`.
- Add opt-in group membership: `research`, `media-work`, `live-browser`, `heavy`, `experimental` (full); bounded subsets in `web-read` and `shared-read`.
- Refresh generated repo harness MCP surfaces via `scripts/sync_agent_stack.py`.
- Update MCP safety/source documentation for scraping, browser deps, and untrusted content.

## Out Of Scope

- Creating first-party MCP server code under `mcp/scrapling/`.
- Adding to default `harness` or remote `tunnel` groups.
- Curated external skill catalog row or live `wagents skills sync --apply`.
- `scrapling mcp --http` transport (MCPHub uses stdio child processes only).
- Home sync (`--targets home --apply`) without explicit approval.

## Affected Users And Tools

- Users of managed repo MCP configs connecting to MCPHub opt-in groups.
- Users who need JS-rendered pages, Cloudflare bypass, or CSS-selector extraction beyond `fetch`/`trafilatura`.

## Risks

- Browser tools spawn Chromium and are CPU/RAM heavy; excluded from default bundles.
- Scraped content is untrusted external data; upstream sanitizes hidden content when `main_content_only=true`.
- Rate limits and robots.txt apply; proxy settings belong in user-owned `.env.mcphub` only.
- Persistent browser sessions must be closed with `close_session` to avoid resource leaks.