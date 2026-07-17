# Validation Matrix

| Surface | Command | Expected Result | Notes |
|---------|---------|-----------------|-------|
| OpenSpec artifacts | `uv run wagents openspec validate` | This change valid; fleet may show foreign fails | CLOSEOUT 2026-07-13: fleet 63/64; **foreign fail** `add-open-websearch-mcp-skill` only. |
| Registry parity | `just mcphub-generate-check` | Settings match registry | ok (closeout). |
| Settings invariants | `bash scripts/mcphub/validate-settings.sh` | exit 0 | ok (closeout). |
| Repo sync | `uv run python scripts/sync_agent_stack.py --targets repo --apply` | MCP mirrors updated | Done during implement; avoid re-apply on mixed dirty tree unless needed. |
| Registry tests | `uv run pytest tests/test_reddit_mcp_buddy_registry.py -q` | pass | **5 passed** (entry, wrapper, groups, exclusions, settings parity). |
| Asset validation | `uv run wagents validate` | pass | All validations passed (closeout). |
| Docs generate | `wagents docs generate --no-installed` | conditional | Skip re-run if mcp index card present (blast-radius). |
| Package probe | MCP Python SDK stdio tools/list | tools_runtime == documented five | **PASS** 2026-07-13 (`browse_subreddit`, `search_reddit`, `get_post_details`, `user_analysis`, `reddit_explain`). |

## Blockers

- None for anonymous-mode registry ship.

## Deferred Checks

- Home sync (`--targets home --apply`)
- Live hub-wide `bash scripts/mcphub/smoke.sh` when hub init is degraded
- Successful runtime `tools/list` (stdio framing fix or hub-mediated after reload)
- Full password-grant OAuth e2e (requires real Reddit script app)
- Promotion into `daily` / `coding` groups
