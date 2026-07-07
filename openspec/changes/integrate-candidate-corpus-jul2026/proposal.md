# Proposal

## Problem

The July 2026 candidate corpus contains hundreds of third-party repositories and
tree targets that may be skills, MCP servers, plugins, tools, docs, or broad
collections. Blindly adding them to repo catalogs would violate the curated
external skill and MCP registry trust gates.

## Intent

Add a deterministic, auditable intake lane plus a trust-gated promotion
research-packet handoff for the corpus. The lane accounts for every raw URL,
normalizes duplicate and tree targets, records public metadata, captures
deep-research/source-support packets, routes docs-steward surfaces, adds
non-installable catalog coverage for every unique target, and keeps every
candidate blocked from live install, repo-native promotion, execution, or
vendoring until promotion gates pass.

The current target state is `research-graph-ready`: all 289 unique normalized
targets remain blocked pending source-list, license, security, attribution,
auth, docs-steward, and target-specific validation gates.

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
- Emit one non-installable curated-external authoring row per unique normalized
  target with no install command and `sync_kind: none`.
- Regenerate the public catalog index/pages and README from the repo-native
  docs pipeline.
- Add focused regression tests for corpus coverage and docs-steward accounting.

## Out Of Scope

- Live `npx skills add`, `wagents skills sync --apply`, or harness installs.
- Executing candidate scripts, MCP servers, package hooks, binaries, or CLIs.
- Vendoring third-party content into `skills/`.
- Adding candidates to default MCPHub groups or default install paths.
- Publishing install commands for unpromoted candidate rows.
- Marking candidates ready for repo promotion or live install before all
  target-specific trust gates pass.
- Executing promotion-wave mutations or renaming catalog-only rows into
  installable rows without passed research packets.
- Pushing commits.

## Risks

- Public Git metadata is not a complete license/security audit.
- Some repositories may be unreachable or renamed between runs.
- Catalog promotion still requires source-list evidence and human trust-gate
  review.
