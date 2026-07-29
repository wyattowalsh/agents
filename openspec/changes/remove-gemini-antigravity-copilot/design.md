# Design: Remove Gemini / Antigravity / Copilot

## Locked decisions

1. **Total active-surface removal:** Drop all three harnesses and their target
   identifiers from `site_model.SUPPORTED_AGENTS`,
   `external_skills.SUPPORTED_TARGET_AGENTS`, adapters, schemas, generated
   commands, public docs, and repo-managed home projections.
2. **Crush MCP:** `render_flat_mcp(..., harness="crush")`; AITK reuses the Crush
   filter; flat map + `type: stdio`; never `render_client_mcp`.
3. **Chrome DevTools:** Crush = `repo_mcp` owner; strip gemini extension +
   Copilot plugin/web rows; rewrite AGENTS.md §2.4.
4. **Dirty WIP:** Preserve `candidate-node` / `candidate-uv-tool` and candidate
   servers in mcp-registry; strip removed harness IDs only.
5. **Delete order:** Stop sync writers before deleting Gemini, Antigravity, and
   Copilot projections, adapters, wrappers, hand rules, and receipt-owned home
   files. Never delete applications or unrelated user-owned data.
6. **Smoke matrix:** Drop `github-copilot` + `gemini-cli` only.
7. **Keep unrelated capabilities:** OpenCode auth plugins, the `gemini-api`
   skill, GitHub repositories/Actions/workflows, and candidate source names are
   not harness integrations and remain.
8. **Taxonomy:** the managed set is exactly `claude-code`, `codex`, `crush`,
   `cursor`, `grok`, and `opencode`; the Skills CLI-native set is exactly
   `claude-code`, `codex`, `crush`, `cursor`, and `opencode`. Cherry Studio,
   LM Studio, ChatGPT, Claude Desktop, and similar clients remain explicitly
   labeled MCP-only or hybrid surfaces and do not inflate either taxonomy.
9. **Residual cleanup:** authored metadata, fixtures, and generated projections
   are in scope when they actively endorse a retired harness. Historical
   records, this change, unrelated GitHub functionality, the `gemini-api`
   skill, and candidate source names require explicit bounded-scan
   classification rather than blanket deletion.
10. **Generation closeout:** AITK must receive the Crush-filtered flat
    `type: stdio` MCP map, and `uv run wagents apm refresh-lock --check` runs
    only after every source-driven generation pass.
11. **No commits** unless user asks.

## Architecture notes

- Sync-MCP owns `scripts/sync_agent_stack.py` then `config/mcp-registry.json`
  serially (same owner; no parallel dual-edit).
- Platforms own `site_model`, `SUPPORTED_TARGET_AGENTS`, inventory, OpenSpec,
  APM, and CLI target normalization as one serialized removal lane.
- Authoring MDX: strip all three target identifiers, remap install commands to
  the remaining harnesses, and preserve the skill rows.
- Retirement scanning is semantic and bounded to active source/generated
  surfaces. It rejects the three retired managed IDs and
  `https://github.com/google/gemini-cli` while retaining reviewed allowlisted
  historical or change-control evidence.

## Rollback

Restore the removed source definitions and re-run Wave 6 generation. Home
rollback may restore only paths backed up by the managed-removal receipt; it
must never wipe or reconstruct unrelated user data.
