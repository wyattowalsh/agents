# Tasks

## Implementation

- [x] Capability matrix via manual maintainer pass (bypass documented).
- [x] Add `scripts/mcphub/reddit-mcp-buddy-stdio.sh` with pin `1.1.13`.
- [x] Add `reddit-mcp-buddy` to `config/mcp-registry.json` with opt-in groups.
- [x] Add `tests/test_reddit_mcp_buddy_registry.py` (registry + wrapper + generated settings parity).
- [x] Update maintainer docs (mcphub.md, mcphub-operator, KB, mcp index, tools surface).
- [x] Regenerate `mcp/mcphub/mcp_settings.json` and repo MCP surfaces.
- [x] Run validation matrix (pytest, generate-check, validate-settings, wagents validate).

## Documentation

- [x] Record audit evidence in `audit-bundle.json` and `tools-list.json`.
- [x] Refresh generated docs surfaces (`wagents docs generate --no-installed`) — already run; closeout avoids re-blast.
- [x] tools.mdx opt-in Reddit aside + operator ~10 rpm throttle note.

## Verification (CLOSEOUT)

- [x] Allowlist existence + wrapper executable.
- [x] npm pin re-verify `1.1.13`.
- [x] pytest 5 passed (registry + wrapper + settings parity).
- [x] `just mcphub-generate-check` ok.
- [x] `bash scripts/mcphub/validate-settings.sh` ok.
- [x] `uv run wagents validate` — all passed.
- [x] OpenSpec fleet validate: **1 foreign fail** = `add-open-websearch-mcp-skill` (not this change); `add-reddit-mcp-buddy` status done.
- [x] Stdio cold-start anonymous banner verified.
- [x] Successful tools/list via Python MCP SDK stdio — runtime names match documented five tools.
- [ ] Optional runtime mcphub-smoke after hub settings reload (deferred; hub root 200, naive JSON tools/list 400 without streamable client).
