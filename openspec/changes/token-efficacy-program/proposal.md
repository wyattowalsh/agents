# Proposal

## Why

A token-efficacy survey identified eight context layers and dozens of candidate tools, but category winners are still unsettled, RTK fleet policy exists without live apply, OpenCode DCP tuning lacks measured evidence, standing context (~980 tok global + skill descriptions) has no trim list, and maintainer docs only partially describe token posture. Applying tools without compare research risks stacking incompatible layers (Sleev vs DCP vs Cozempic vs Headroom vs mcp-compressor vs jCodeMunch).

This program extends [`integrate-rtk-harness-fleet`](../integrate-rtk-harness-fleet/tasks.md) Wave 4 (T040–T044) with research gates, measured rollout, and docs-steward enrichment under explicit OpenSpec governance.

## What Changes

- OpenSpec artifacts under `openspec/changes/token-efficacy-program/`.
- **Research (read-only):** `/research compare` per missing category, `/research` + `/host-panel` for MCP schema tax, `/research` + `/review` for standing-context trim candidates, `/research track token-oss-landscape`, and OpenCode DCP log review.
- **RTK live apply (gated):** `RTK_TELEMETRY_DISABLED=1 uv run wagents rtk sync --apply --platforms claude-code,cursor,opencode,codex,gemini-cli,github-copilot` after `wagents rtk doctor` passes.
- **Wave 4 completion:** T040–T044 from `integrate-rtk-harness-fleet` (sync `--with-rtk`, Grok shim, catalog/docs, no `@RTK.md` validation, `rtk gain --history` lane).
- **Docs:** `/docs-steward` enrichment of `AGENTS.md` token section, harness-config hub MDX, `wagents readme`, and sync projections.
- **Research journals:** outputs under `~/.claude/research/` (track + compare artifacts).

## Impact

- Maintainers get a decision matrix with winner, runner-up, non-stacking notes, and explicit install gates before any new OSS.
- RTK shell dedup moves from policy-only to live fleet hooks with `rtk gain` measurement.
- Public docs describe layer taxonomy, decision gates, and pointers to RTK, DCP, and MCPHub posture.
- Standing context trim candidates become evidence-backed rather than ad hoc edits.

## Scope

- OpenSpec scaffold (Wave 0), parallel research waves (Wave 1), RTK apply + T040–T044 (Wave 2), docs-steward (Wave 3), conditional DCP tuning (Wave 4), validation (Wave 5).
- Spec deltas for downstream tooling and docs-instructions surfaces.

## Out Of Scope (until gated)

- Installing Sleev, Headroom, Cozempic, mcp-compressor, jCodeMunch, or other surveyed OSS without post-research approval and explicit maintainer sign-off.
- `@RTK.md` in shared instruction corpus (`instructions/global.md`, `AGENTS.md` bridges).
- RTK in `opencode.json` plugin array.
- Commits, branch creation, or live `wagents skills sync --apply` during Wave 0 scaffold.

## Risks

| Risk | Mitigation |
| --- | --- |
| Tool stacking causes regressions or double-pruning | One primary tool per layer; measure with `rtk gain` + DCP stats before stacking; decision gates in design |
| RTK init cross-effects (Cursor init touches Claude assets) | Doctor + dry-run first; telemetry disabled; explicit platform list |
| Research recommends installs before gates | Install policy: research + docs now; no OSS until compare/host-panel outputs approve each category |
| DCP tuning breaks model-neutral policy | Tune only if R5 shows compaction pain; stay model-neutral per AGENTS.md §2.3 |
| Docs drift from live harness state | docs-steward Mode A + `wagents readme --check` + `wagents docs build` in Wave 5 |
| Grok RTK shim without schema proof | T041 remains blocked until live Grok hook I/O is verified |
