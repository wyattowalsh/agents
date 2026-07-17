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

The target public state is `stable-catalog-reconciled`: all 293 raw entries and
289 unique normalized targets retain internal traceability, while all 289 targets
resolve through stable, non-candidate public catalog identities. Coverage is
classified exactly as 121 existing installable owners, 6 existing
inspection-required owners, 158 generated stable references, and 4 generated
stable hard-quarantine references. The generated stable-reference count is 162,
and public authoring, index, and detail-page counts for `candidate-corpus-*` are
zero.

Catalog integration and installability are separate dimensions. Reviewed Skills
CLI selectors may remain installable curated-external rows with recorded local
evidence, but source-level coverage does not become installable merely because a
stable catalog reference exists.

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
- Reconcile all 289 unique targets to stable non-candidate catalog ownership:
  preserve 121 existing installable owners and 6 existing inspection-required
  owners, then generate 158 stable references plus 4 stable hard-quarantine
  references.
- Remove source-authored and generated public `candidate-corpus-*` rows after
  stable ownership is proven; the planning manifests retain raw and normalized
  corpus provenance.
- Track installable selector rows and source-level integration coverage
  independently so a reference row never implies install eligibility.
- Bind all four hard-quarantine sources into the central security quarantine
  register. Allow attributed docs-only references with no command or sync target,
  while rejecting install, execution, or default enablement.
- Regenerate the public catalog index/pages and README from the repo-native
  docs pipeline.
- Add focused regression tests for corpus coverage and docs-steward accounting.
- Record live local install evidence for promoted selectors across supported
  harness roots without committing secrets or enabling credentialed services by
  default.
- Record the explicitly authorized post-intake runtime overlay for audited CLIs,
  libraries, MCP servers, and native plugins. Pin package versions or source
  commits, keep credentialed and high-risk services inert, and emit one
  secret-free runtime disposition for every normalized target.

## Out Of Scope

- Running candidate MCP tools, long-lived services, browsers, device automation,
  credential flows, provider-spend actions, or project/data mutations during
  assurance.
- Installing or executing unreviewed, unpinned, quarantined, or policy-conflicting
  artifacts. Audited native dependency builds and bounded version/help probes are
  permitted only in the explicitly authorized runtime overlay.
- Vendoring third-party content into `skills/`.
- Adding candidates to default MCPHub groups or default install paths.
- Publishing install commands for unreviewed or terminal-gated candidate rows.
- Treating stable catalog coverage as permission to install or execute a source.
- Marking candidates ready for repo promotion or live install before all
  target-specific trust gates pass.
- Pushing commits.

## Risks

- Public Git metadata is not a complete license/security audit.
- Some repositories may be unreachable or renamed between runs.
- Terminal reference/skip rows can only become installable in a future wave if
  the missing license, source access, safety, auth, or product-choice blocker is
  explicitly resolved.
- Stable-id collisions or unreviewed renames can overwrite catalog ownership;
  reconciliation must prove one owner per target before removing candidate ids.
- Package lifecycle scripts and plugin hooks can mutate host or project state;
  allow only audited native builds, keep broad-hook plugins disabled, and record
  exact activation state in the non-skill assurance artifact.
