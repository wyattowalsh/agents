# Proposal

## Problem

The managed MCP registry does not include `open-websearch`, so repo and home harness configs cannot expose a no-API-key multi-engine web search and page/README fetch surface consistently across supported tools.

This affects canonical MCP configuration, curated external skill catalog coverage, and generated downstream harness surfaces, so the change needs OpenSpec tracking instead of a direct trivial edit.

## Intent

Add `open-websearch` once to the normalized registry using an npx stdio launch wrapped by repo-managed fleet-safe defaults, wire opt-in MCPHub groups (not default `harness` or `tunnel`), and record the upstream skill in the curated external catalog.

## Scope

- Add `open-websearch` as an enabled stdio MCP server launched via `scripts/mcphub/open-websearch-stdio.sh`.
- Add opt-in group membership: `web-search`, `research`, `experimental` (full); bounded subsets in `web-read` and `shared-read`.
- Author `docs/src/authoring/skills/open-websearch.mdx` (catalog only; no vendor copy in `skills/`).
- Refresh generated repo harness MCP surfaces via `scripts/sync_agent_stack.py`.
- Update MCP safety/source documentation for scraping, optional Playwright, and proxy overrides.

## Out Of Scope

- Creating first-party MCP server code under `mcp/open-websearch/`.
- Adding to default `harness` or remote `tunnel` groups.
- Live `wagents skills sync --apply` or committed proxy secrets.
- Playwright install or `FETCH_WEB_INSECURE_TLS=true` in tracked config.

## Affected Users And Tools

- Users of managed repo MCP configs for Codex, Cursor, Grok, OpenCode, GitHub Copilot CLI, Gemini CLI, Antigravity, Cherry Studio, and related generated surfaces.
- Users who want API-key-free multi-engine search and article/README fetch via MCPHub opt-in groups.

## Generated Surfaces To Refresh

- `mcp/mcphub/mcp_settings.json`
- `mcp.json`, `.vscode/mcp.json`, `opencode.json`, `config/codex-config.toml`, Grok/Cursor MCP mirrors
- `docs/public/generated-registries/skills-catalog-index.json` and catalog pages via `uv run wagents docs generate`

## Risks

- Scraping-based engines may hit rate limits or ToS constraints; prefer duckduckgo/startpage defaults in the wrapper.
- Optional Playwright path can download Chromium; wrapper sets `SEARCH_MODE=request` by default.
- Fetched page content is untrusted external data; upstream skill documents prompt-injection mitigations.