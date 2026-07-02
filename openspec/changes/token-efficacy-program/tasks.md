# Tasks

## Wave 0 — OpenSpec Scaffold

- [x] T000 Create `openspec/changes/token-efficacy-program/` with proposal, design, tasks, validation-matrix, affected-surfaces, and spec deltas.
- [x] T001 Run `uv run wagents openspec validate` (includes this change package).

## Wave 1 — Research (parallel, read-only) `[P]`

- [ ] T010 `[P]` R1 — `/research compare` per missing category; deliver decision matrix (winner, runner-up, why, non-stacking vs RTK + DCP).
- [ ] T011 `[P]` R2 — `/research` + `/host-panel` MCP schema tax strategy (groups vs compressor vs registry split).
- [ ] T012 `[P]` R3 — `/research` + `/review` standing-context trim candidates (skills, rules, descriptions).
- [ ] T013 `[P]` R4 — `/research track token-oss-landscape`; journal + STATE block under `~/.claude/research/`.
- [ ] T014 `[P]` R5 — Review OpenCode DCP logs (`~/.config/opencode/logs/dcp/`), `/dcp stats`, token-monitor; summarize compaction pain.
- [ ] T015 Synthesize decision gates from R1–R5; document approve/deny per category (no installs in recommendations until gates pass).

### Wave 1 compare matrix (R1 scope)

| Layer | Compare set | Primary harness |
| --- | --- | --- |
| Session pruners | Sleev vs DCP (keep) vs Cozempic vs context-mode | OpenCode / Claude |
| Cross-harness proxy | Headroom vs Sleev vs LeanCTX | Cursor, Codex, OpenCode |
| MCP schema tax | mcp-compressor vs Tool Attention vs groups-only | MCPHub fleet |
| Code reads | jCodeMunch vs symbol-index MCPs vs policy-only | All |
| Shell dedup | RTK vs LeanCTX | RTK installed — overlap check only |

## Wave 2 — RTK Live Apply (after doctor ok)

- [ ] T020 Run `uv run wagents rtk doctor --format json`; block apply on fail.
- [ ] T021 `RTK_TELEMETRY_DISABLED=1 uv run wagents rtk sync --apply --platforms claude-code,cursor,opencode,codex,gemini-cli,github-copilot`.
- [ ] T022 Run `uv run wagents rtk gain --graph` for post-apply baseline.
- [ ] T040 Add optional `--with-rtk` / `RTK_ENABLED=1` to `scripts/sync_agent_stack.py` (from `integrate-rtk-harness-fleet`).
- [ ] T041 Implement Grok custom RTK hook only after live Grok hook schema proof.
- [ ] T042 Add docs or catalog entry for RTK if maintainers want public surfacing.
- [ ] T043 Add no-stale-include validation for `@RTK.md` in shared instruction surfaces.
- [ ] T044 Add usage-review lane for `rtk gain --history` and missed savings.

## Wave 3 — Docs Steward

- [ ] T030 `/docs-steward` Mode A — enrich `AGENTS.md` token budget, layer taxonomy, decision gates, RTK/DCP/MCPHub pointers.
- [ ] T031 Add or extend harness-config token posture hub MDX under `docs/src/content/docs/harness-config/`.
- [ ] T032 Run `uv run wagents readme` + `uv run wagents docs generate --no-installed` + `uv run wagents docs build`.
- [ ] T033 Run `uv run python scripts/sync_agent_stack.py --apply --targets repo` for Copilot/Cursor projections.

## Wave 4 — DCP Tuning (conditional)

- [ ] T040 Review R5 evidence; skip wave if no compaction pain or threshold mismatch.
- [ ] T041 Tune `config/opencode-dcp.jsonc` if warranted (stay model-neutral per AGENTS.md §2.3).
- [ ] T042 Re-run DCP stats / log spot-check after any tune.

## Wave 5 — Validation

- [ ] T050 Run `uv run wagents rtk doctor --format json`.
- [ ] T051 Run `uv run wagents rtk gain --graph` (or `--history` when T044 lane exists).
- [ ] T052 Run DCP stats / log spot-check if Wave 4 ran.
- [ ] T053 Run `uv run wagents validate`.
- [ ] T054 Run `uv run pytest tests/test_rtk_cli.py -q`.
- [ ] T055 Run `uv run wagents docs build` && `uv run wagents readme --check`.
- [ ] T056 Run `uv run wagents openspec validate`.
- [ ] T057 Inspect final diff; confirm no unrelated dirty state was reverted; confirm no ungated OSS installs.
