# Proposal

## Problem

The July 2026 candidate corpus contains hundreds of third-party repositories and
tree targets that may be skills, MCP servers, plugins, tools, docs, or broad
collections. Blindly adding them to repo catalogs would violate the curated
external skill and MCP registry trust gates.

## Intent

Add a deterministic, auditable intake lane, then apply the reviewed promotion
overlay for every source that passed source-list, license, security,
attribution, auth, dedupe, and docs-steward gates. The lane accounts for every
raw URL, normalizes duplicate and tree targets, records public metadata,
captures deep-research/source-support packets, routes docs-steward surfaces,
and preserves terminal blockers for candidates that cannot be safely installed
or enabled.

The current target state is `promotion-overlay-installed`: all 293 raw entries
and 289 unique normalized targets have terminal decisions. Reviewed Skills CLI
selectors are installable curated-external catalog rows with live local install
evidence, while remaining rows are explicit terminal reference/skip decisions.

## Scope

- Track the raw candidate corpus under `planning/manifests/candidate-corpus-jul2026/`.
- Extend `scripts/generate_candidate_corpus_shards.py` into the corpus
  normalizer, shard-map emitter, public-metadata auditor, and coverage checker.
- Emit source research, source support, security, license, compliance/auth,
  docs impact, dedupe, integration decision, validation, and final review
  artifacts.
- Emit promotion research handoff artifacts:
  `research-task-graph.json`, `research-packet-schema.json`,
  `raw-research-packets.json`, `unique-target-research-packets.json`,
  `subagent-wave-queue.json`, `promotion-readiness-queue.json`,
  `promotion-gate-matrix.json`, `live-install-command-preview.json`,
  `existing-integration-coverage.json`, `promotion-wave-plan.json`,
  `promotion-wave-plan.md`, `full-integration-progress.json`, and
  `full-integration-state.md`.
- Emit curated-external authoring rows for every unique normalized target:
  reviewed selectors become installable rows, and terminal gated sources remain
  non-syncing reference rows.
- Regenerate the public catalog index/pages and README from the repo-native
  docs pipeline.
- Add focused regression tests for corpus coverage and docs-steward accounting.
- Record live local install evidence for promoted selectors across supported
  harness roots without committing secrets or enabling credentialed services by
  default.

## Out Of Scope

- Executing candidate scripts, MCP servers, package hooks, binaries, or CLIs.
- Vendoring third-party content into `skills/`.
- Adding candidates to default MCPHub groups or default install paths.
- Publishing install commands for unreviewed or terminal-gated candidate rows.
- Marking candidates ready for repo promotion or live install before all
  target-specific trust gates pass.
- Pushing commits.

## Risks

- Public Git metadata is not a complete license/security audit.
- Some repositories may be unreachable or renamed between runs.
- Terminal reference/skip rows can only become installable in a future wave if
  the missing license, source access, safety, auth, or product-choice blocker is
  explicitly resolved.
