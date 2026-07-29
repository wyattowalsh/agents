# Gate G8 / Definition of Done — remove-three-harnesses

## Gate status

| Gate | Status | Notes |
| --- | --- | --- |
| G−1 Preflight + OpenSpec | **PASS** | OpenSpec change `remove-gemini-antigravity-copilot`; dirty-map recorded; no commits |
| G1 Discovery | **PASS** | Inventories under `planning/manifests/remove-three-harnesses/` |
| G2 SSOT + Crush smoke | **PASS** | AITK uses `render_flat_mcp(..., harness="crush")`, `type: stdio` |
| G3 Registries/corpus | **PASS** | Secondary registries stripped (re-applied after parallel-wave restores) |
| G4 Deletes | **PASS** | Bridges/wrappers/rules/Copilot `.github` projections removed; candidates kept |
| G5 MDX + toolkit | **PASS** | Authoring frontmatter stripped; toolkit/pentest updated |
| G6 Regen | **PENDING FINAL REPLAY** | Current source edits invalidate the earlier docs/readme/sync/APM snapshot |
| G7 Test surgery | **PENDING FINAL REPLAY** | Earlier focused result is historical until the settled source snapshot is retested |
| G8 Validate + canaries | **PENDING FINAL REPLAY** | Final hooks/parity/canaries/validate evidence must bind the settled tree |

## Canaries

- **W8.C.1 Crush:** source contract uses Crush-filtered `type: stdio`; final regression replay pending.
- **W8.C.2 Clients:** Cherry Studio / LM Studio / Claude Desktop / ChatGPT source projections remain; final replay pending.
- Managed/curated taxonomy: all three retired IDs absent in source; generated replay pending.
- OpenCode auth plugins (`opencode-gemini-auth`, `opencode-antigravity-auth`, `opencode-claude-auth`) — **KEPT**
- `gemini-api` authoring row — **KEPT**
- Candidate wrappers `candidate-node` / `candidate-uv-tool` — **KEPT**
- Smoke matrix: `github-copilot` + `gemini-cli` dropped — **GREEN**

## Blockers / dirty-tree notes

1. ~~Stale EXT-085…088 quarantine validate blockers~~ — **CLEARED** in cleanup-v7 W1a (`quarantine-align` NO-OP; live collector 0 errors; validate exit 0). No invent MDX; quarantine not weakened.
2. Parallel subagent waves intermittently restored deleted platform modules / registries; final state was re-locked in-session.
3. `scripts/sync_agent_stack.py` may still contain unused dead helpers for Copilot/Gemini render paths; live call sites for removed harnesses are gone.
4. **No git commits** (per plan / user).

## DoD checklist

- [x] Repo no longer endorses the three in install/docs/sync/hooks/RTK platforms (SSOT)
- [x] Curated external target validation rejects all three
- [x] Crush (+ AITK) Crush-shaped MCP with `type: stdio`
- [x] Chrome matrix + AGENTS.md §2.4; Crush = `repo_mcp`
- [x] Candidate MCP WIP preserved
- [x] Copilot `.github` projections gone; CI workflows kept; smoke drops 2 ids
- [x] Authoring install endorsements stripped
- [x] OpenCode auth + `gemini-api` kept
- [ ] APM lock refreshed; hooks validate + parity green on the settled snapshot
- [ ] Canaries W8.C.1–2 green on the settled snapshot
- [x] No commits
- [ ] Full `wagents validate` clean on the settled snapshot (the prior cleanup-v7 log is historical evidence only)
