# RV MCP Findings Closure

Completed: 2026-07-06

## Finding closure matrix

| RV | Status | Proof |
|----|--------|-------|
| RV-001 | Closed | `scrapling` shipped in `1130bbfc`; docs/skills/registry aligned |
| RV-002 | Closed | Atomic commits: ddgs pin (this wave), wagents inventory (separate) |
| RV-003 | Closed | `mcp-registry.mdx` prose + `--regen-configs` embed includes `scrapling` |
| RV-004 | Closed | `ddgs-mcp-server==0.5.1` in registry + `tests/test_ddgs_registry.py` |
| RV-005 | Closed | `wagents validate` passes; `add-ddgs-mcp` archived (`2026-07-06-add-ddgs-mcp`); `docs build` waived (`starlight-site-graph`) |
| RV-006 | Closed | Documented: tunnel never included `ddgs` (commit message inaccuracy only) |
| RV-007 | Closed | `_merge_local_skill_roots_into_query` + skills_sync aggregate failures + tests |
| RV-008 | Closed | Targeted `write_site_data` / `write_index_page` / `write_surfaces_pages` regen |

## Verification evidence

- `just mcphub-generate-check` — pass
- `just mcphub-validate` — pass
- `sync_agent_stack --targets repo --check` — pass
- `uv run wagents validate` — pass
- `uv run pytest tests/test_scrapling_registry.py tests/test_ddgs_registry.py` — pass
- `uv run wagents docs build` — **waived** (`starlight-site-graph`)
- `just mcphub-smoke` — pass (2026-07-06, bearer auth via runtime `bearerKeys`)
- `/mcp/ddgs` `tools/list` — pass: `ddgs-search_text`, `ddgs-search_news` (2 tools)
- `uv run wagents openspec archive add-ddgs-mcp --apply -y` — archived as `2026-07-06-add-ddgs-mcp`

## Runtime notes

- Clean single MCPHub instance required: overlapping LaunchAgent + `just mcphub-up` processes caused transient `groups.find` fatals and HTTP 401/empty-reply smoke failures.
- `scrapling` cold-start can exceed 5 minutes (playwright/patchright downloads); prior session logs show 10 tools after connect. Out of scope for `add-ddgs-mcp` archive.

## OpenSpec blockers (out of scope)

Four other active OpenSpec changes still fail repo-wide `openspec validate`; unrelated to ddgs/scrapling remediation.