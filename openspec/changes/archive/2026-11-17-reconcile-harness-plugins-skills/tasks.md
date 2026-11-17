# Tasks

## G0 — Evidence Foundation

- [x] T-000 — coordinator — `planning/manifests/harness-reconciliation.json` — freeze current local evidence with terminal dispositions.
- [x] T-010 [P] — skills desired — `scripts/generate_harness_reconciliation.py` — default desired sync has zero missing rows.
- [x] T-020 [P] — skills one-off — manifest matrix — installed-external rows are preserved unless explicitly promoted.
- [x] T-030 [P] — skills unprovenanced — manifest matrix — read-only discovered rows stay local-only.
- [x] T-040 [P] — Codex/Claude plugins — manifest matrix — native plugin/cache state is classified.
- [x] T-050 [P] — OpenCode plugins — manifest matrix — repo/live/TUI plugin drift is classified.
- [x] T-060 [P] — Gemini/Grok plugins — manifest matrix — extension config blockers and native plugin state are classified.
- [x] T-070 — parallel shard graph — manifest task graph — 156 row-addressable shards split by harness, asset type, action, owner, and source.
- [x] T-080 — validation — `tests/test_harness_reconciliation.py` — static manifest checks enforce coverage, graph aggregation, and redaction.

## Verification

- [x] Run `uv run python scripts/generate_harness_reconciliation.py`.
- [x] Run `uv run pytest tests/test_harness_reconciliation.py -q`.
- [x] Run `uv run wagents validate`.
- [x] Run `uv run wagents catalog index --check --format json`.
- [x] Run `uv run wagents openspec validate`.
- [x] Run `uv run wagents skills sync --dry-run --format json`.

## Stop Rules

- Do not run `wagents skills sync --apply`.
- Do not run live `npx skills add`.
- Do not delete or refresh plugin caches.
- Do not write home harness config.
