# Tasks

## Implementation

- [x] Track the raw candidate corpus.
- [x] Normalize raw GitHub URLs, fragments, tree paths, and duplicates.
- [x] Emit per-candidate records with requested manifest fields.
- [x] Emit shard, cluster, source research, source support, security, license,
  compliance/auth, docs impact, dedupe, decision, validation, and final review
  artifacts.
- [x] Emit 289 non-installable curated-external catalog authoring rows.
- [x] Add corpus coverage tests.

## Documentation

- [x] Add docs-steward surface summary.
- [x] Add decision log for risky, skipped, deduped, and quarantined sources.
- [x] Add changelog entry under the candidate-corpus manifest.
- [x] Add validation and final review reports.
- [x] Regenerate catalog index, catalog pages, and README.

## Promotion Research Packet Handoff

- [x] Emit `research-task-graph.json` with 293 raw lanes, 289 unique target
  lanes, and 7,879 leaf checks.
- [x] Emit `research-packet-schema.json` with required packet fields and
  raw/unique leaf suffixes.
- [x] Emit `raw-research-packets.json` and
  `unique-target-research-packets.json` for read-only packet dispatch.
- [x] Emit `subagent-wave-queue.json` for read-only packet dispatch.
- [x] Emit `promotion-readiness-queue.json` showing 0 ready for repo
  promotion, 0 ready for live install, and 289 blocked until trust gates.
- [x] Emit `promotion-gate-matrix.json` and
  `live-install-command-preview.json` with no live install commands.
- [x] Emit `existing-integration-coverage.json` so existing installable rows
  are merged instead of duplicated.
- [x] Emit `promotion-wave-plan.json` and `promotion-wave-plan.md` assigning
  every unique target to exactly one trust-gated wave.
- [x] Emit `full-integration-progress.json` and `full-integration-state.md`
  with `complete: false` and `research-graph-ready`.
- [x] Complete source-list, license, security, attribution, auth,
  docs-steward, dedupe, and target validation packets for promotion waves.
- [x] Promote or adapt only targets whose completed packets pass all gates.
- [x] Record read-only deep source audit evidence for every normalized target
  without executing candidate code.
- [x] Record 1038 promoted installable curated-external rows and live local
  install evidence across supported harness roots.
- [x] Preserve 175 remaining rows as explicit terminal trust-gated
  reference/skip decisions.

## Verification

- [x] `uv run python scripts/generate_candidate_corpus_shards.py --check-coverage`
- [x] `uv run python scripts/promote_candidate_corpus.py --write --check-coverage`
- [x] `uv run pytest tests/test_candidate_corpus.py -q`
- [x] `uv run ruff check scripts/generate_candidate_corpus_shards.py scripts/promote_candidate_corpus.py tests/test_candidate_corpus.py`
- [x] `uv run wagents validate`
- [x] `uv run wagents docs generate --no-installed`
- [x] `uv run wagents readme`
- [x] `uv run wagents readme --check`
- [x] `uv run wagents skills sync --dry-run`
- [x] `uv run wagents docs lint` returned warnings only.
- [x] `uv run wagents docs build`
- [x] `OPENSPEC_TELEMETRY=0 npx -y @fission-ai/openspec@latest validate integrate-candidate-corpus-jul2026 --strict --json`
- [x] `uv run python scripts/audit_candidate_deep_sources.py --check`
- [x] `uv run python scripts/promote_candidate_corpus.py --final-check`
- [x] `uv run python scripts/apply_candidate_corpus_promotions.py --check`
- [x] `uv run wagents openspec validate`
