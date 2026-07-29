# Tasks: cursor-grok-high-pin

## Wave 0 — discovery (RO)

- [x] D0-a: Inventory overlay/schema/agents/rule (confirm High pin + agent count)
- [x] D0-b: Residual `inherit` / non-pin grep (classified path:line list)
- [x] D0-c: Prove sync early-return + allowlisted rules fix site
- [x] D0-d: tooling-policy warrant → SKIP dead `model_defaults.cursor`
- [x] D0-e: Test gap map for W1-H modules
- [x] D0-f: Local app inventory (`cli-config.json`, settings, `state.vscdb` keys)
- [x] D0-g: Home drift forecast (orphans / unmarked agents)

## Wave 1 — writers

- [x] W1-F0: Scaffold this OpenSpec change (proposal/design/tasks/surfaces/matrix/delta)
- [x] W1-A: Rewrite `.cursor/rules/cursor-models.mdc` — always High; ban omit/fast/inherit
- [x] W1-B: `wagents/platforms/cursor.py` default → `cursor-grok-4.5-high`
- [x] W1-C: Fix `sync_home_targets` Cursor-only path + allowlisted rules (no orphan deletes)
- [x] W1-D: Managed-marker home agents → `~/.cursor/agents/` + sync-manifest
- [x] W1-E1: Phase A `preToolUse` Task rewrite (fail-open)
- [x] W1-F/G/I: Live OpenSpec flip + KB + harness-surface / AGENTS notes
- [x] W1-H1/H2/H3: Tests for renderer, sync allowlist, hooks

## Wave 2 — local + sync + Phase B

- [ ] W2-L1: operators SHOULD set `~/.cursor/cli-config.json` `exploreSubagentModel: inherit` (user-owned; sync SHALL NOT write) — operator residual
- [ ] W2-L2: IDE picker = Grok 4.5 High (no live `state.vscdb` writes; sync SHALL NOT write) — user-owned residual
- [x] W2-G1: Home dry-run; abort on unexpected removes
- [x] W2-G2: Repo apply `--platforms cursor`
- [x] W2-G3: Home apply `--platforms cursor`
- [x] W2-E2: Phase B `subagentStart` allowlist deny (after smoke)
- [x] RV-S: Phase B `failClosed: false` projection + render/dispatcher smoke tests

## Wave 3 — validate (parallel)

- [x] `uv run wagents validate`
- [x] Focused `uv run pytest`
- [x] `uv run ruff check` on touched Python
- [x] `uv run ty check` if gated (pre-existing unrelated diagnostics remain outside pin paths)
- [x] `uv run wagents openspec validate`
- [ ] Local verify: CLI inherit + IDE High + home rule/agents present — W2-L1/W2-L2 still operator-owned

## Wave 4 — synthesis

- [x] Project + home agents all `model: cursor-grok-4.5-high`
- [x] Zero `model: inherit` under `.cursor/` + cursor-agents.json
- [x] Hooks rendered; OpenSpec + KB match code
- [x] Residuals recorded (Cloud/dashboard; APM re-sync) — residual: operator SHOULD CLI inherit (W2-L1) + live IDE picker (W2-L2); sync SHALL NOT write `cli-config`/`state.vscdb`

> RV-S close-out: Phase B fail-open projection, render/dispatcher smoke tests, renderer hard-pin, hooks hub prose + pin cards + layer matrix SSOT, OpenSpec CLI inherit softened to operator SHOULD, and checkbox audit completed via fix-all-RV-S plan (RV-S-012∪014).
