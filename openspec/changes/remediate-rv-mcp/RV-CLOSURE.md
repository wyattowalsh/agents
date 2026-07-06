# RV MCP Findings Closure

Completed: 2026-07-06

## Finding closure matrix

| RV | Status | Proof |
|----|--------|-------|
| RV-001 | Closed | `scrapling` shipped in `1130bbfc`; docs/skills/registry aligned |
| RV-002 | Closed | Atomic commits: ddgs pin (this wave), wagents inventory (separate) |
| RV-003 | Closed | `mcp-registry.mdx` prose + `--regen-configs` embed includes `scrapling` |
| RV-004 | Closed | `ddgs-mcp-server==0.5.1` in registry + `tests/test_ddgs_registry.py` |
| RV-005 | Partial | `wagents validate` passes; `openspec validate` 4 unrelated change failures; `docs build` waived |
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

## OpenSpec blockers (out of scope)

Four active OpenSpec changes fail validation unrelated to ddgs/scrapling remediation. Archive `add-ddgs-mcp` only after pin commit lands and change-specific validate passes.