# Tasks

## Implementation

- [x] Track the raw candidate corpus.
- [x] Normalize raw GitHub URLs, fragments, tree paths, and duplicates.
- [x] Emit per-candidate records with requested manifest fields.
- [x] Emit shard, cluster, source research, source support, security, license,
  compliance/auth, docs impact, dedupe, decision, validation, and final review
  artifacts.
- [x] Seed source-level catalog identities for stable ownership reconciliation.
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
- [x] Record 1267 promoted installable curated-external rows and live local
  install evidence across supported harness roots.
- [x] Retire the pre-reconciliation 174 terminal candidate rows after stable
  ownership records and installable overlays are materialized.

## Stable Public Catalog Reconciliation

- [x] Partition all 289 unique targets exactly into 121 existing installable,
  6 existing inspection-required, 158 generated stable references, and 4
  generated stable hard-quarantine references.
- [x] Generate exactly 162 stable source-level reference rows with non-candidate
  ids, `sync_kind: none`, and no install command.
- [x] Preserve installable selector rows as a separate overlay rather than
  counting them as source-level integration ownership.
- [x] Add the four hard-blocked source/tree targets to the central quarantine
  register with explicit exception reviews and no install/default enablement.
- [x] Teach quarantine validation to allow attributed docs-only hard-block rows
  while continuing to reject installable, executable, or default-enabled use.
- [x] Remove all public `candidate-corpus-*` authoring rows only after stable
  ownership and collision checks pass.
- [x] Regenerate the catalog index and detail pages with zero public
  `candidate-corpus-*` rows.
- [x] Update manifest summaries and reports to the stable 121/6/158/4
  classification and 162 generated-reference count.
- [x] Add regression coverage for stable ids, exact partitioning, rename/removal
  safety, quarantine enforcement, and installability separation.

## Authorized Runtime Integration

- [x] Audit package metadata, lifecycle scripts, executable entrypoints, native
  plugins, MCP launchers, auth names, and unsafe probe behavior before install.
- [x] Install the remaining pinned CLI/library distributions into user-owned
  package roots without storing credentials.
- [x] Reconcile existing Bun and skill-bundled commands into the managed
  `~/.local/bin` PATH surface without substituting unrelated packages.
- [x] Install Axiom and HyperFrames native Codex plugins from pinned upstream
  sources and leave their broad-hook surfaces disabled.
- [x] Register candidate MCP launchers with pinned package versions,
  placeholder-only optional auth, and `enabled: false` outside default groups.
- [x] Add a pinned MCPHub 1.0.24 launcher with a process-local loopback bind
  shim and a doctor assertion that rejects wildcard listeners.
- [x] Emit `non-skill-install-assurance.json` with one row per normalized target
  and 63/63 verified CLI, MCP, plugin, or library runtime artifacts.
- [x] Reconcile final record artifact types from the deep source audit and bind
  every raw record plus the progress/final reports to non-skill assurance.

## Verification

- [x] `uv run python scripts/generate_candidate_corpus_shards.py --check-coverage`
- [x] `uv run python scripts/promote_candidate_corpus.py --check-coverage`
- [x] `uv run python scripts/promote_candidate_corpus.py --final-check`
- [x] `uv run python scripts/apply_candidate_corpus_promotions.py --check`
- [x] `uv run pytest tests/test_candidate_corpus.py tests/test_validate_repo.py -q`
- [x] `uv run ruff check scripts/generate_candidate_corpus_shards.py scripts/promote_candidate_corpus.py scripts/apply_candidate_corpus_promotions.py tests/test_candidate_corpus.py`
- [x] `uv run wagents validate`
- [x] `uv run wagents catalog index --check`
- [x] `uv run wagents docs generate --no-installed --check`
- [x] `uv run wagents readme --check`
- [x] `uv run wagents skills sync --dry-run`
- [x] `uv run wagents docs lint`
- [x] `uv run wagents docs build`
- [x] `OPENSPEC_TELEMETRY=0 npx -y @fission-ai/openspec@latest validate integrate-candidate-corpus-jul2026 --strict --json`
- [x] `uv run python scripts/record_candidate_non_skill_assurance.py --check`
- [x] `uv run python scripts/generate_mcphub_settings.py --check`
- [x] `uv run pytest -q tests/test_candidate_corpus.py tests/test_generate_mcphub_settings.py`
- [x] `uv run pytest -q tests/test_mcphub_loopback_bind.py`
- [x] `uv run pytest -q` (2183 passed, 1 skipped)
- [x] `just mcphub-doctor` reports a loopback-only live listener after restart
- [x] `just mcphub-smoke` verifies the all-server, DDGS, and harness endpoints

Global all-change OpenSpec validation currently reports 63 passed and one
unrelated failure: `add-reddit-mcp-buddy` has no specification delta. The
candidate-corpus change itself passes strict validation.
