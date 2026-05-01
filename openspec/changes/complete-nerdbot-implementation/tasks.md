# Tasks

## Foundation

- [x] Add OpenSpec artifacts for the Nerdbot completion change.
- [x] Reconcile public skill contract, local `AGENTS.md`, references, and validation lists so advertised behavior matches implementation progress.
- [x] Remove eval duplication/drift risks and add adversarial untrusted-content coverage.

## Safety Core

- [x] Harden vault-relative path validation across write, source, watch, replay, and generated-output consumers.
- [x] Add crash-durable atomic write and append-only JSONL/Markdown writer primitives.
- [x] Add operation journal helpers with rollback/replay metadata and tests.
- [x] Replace direct script-only safety code paths with package-level primitives while preserving script compatibility.

## CLI And Workflows

- [x] Complete CLI JSON contracts and human output for all advertised mode families.
- [x] Implement source ingestion for local files, directories, text/Markdown, oversized pointer stubs, and optional adapters.
- [x] Implement enrich and derive workflows with provenance, confidence, freshness, and review queue records.
- [x] Implement audit/lint expansion for vault structure, links, frontmatter, source maps, generated artifacts, and safety contracts.

## Retrieval And Graph

- [x] Implement lexical plus SQLite FTS5/BM25 retrieval with source-grounded result records.
- [x] Implement optional semantic retrieval extra with actionable missing-extra errors.
- [x] Implement graph extraction and analytics outputs as rebuildable derived artifacts.
- [x] Preserve Obsidian aliases, heading links, block refs, embeds, and Markdown links in graph/retrieval metadata.

## Obsidian Productization

- [x] Add rich frontmatter, Dataview-friendly dashboards, evidence ledger, review queue, and starter onboarding pages.
- [x] Enforce canonical wikilink and source ID policies in templates and generated pages.
- [x] Document trusted/untrusted content boundaries in user-facing instructions.

## Tests And Validation

- [x] Fix import-order coupling in Nerdbot tests.
- [x] Add path, journal, CLI JSON, package, retrieval, graph, watch, replay, and optional-extra tests.
- [x] Add evals for no-confirmation safety, adversarial KB content, retrieval provenance, and migration dry-run behavior.
- [x] Run the full validation matrix before completion.

## Documentation And Release Surfaces

- [x] Update references, local README, generated docs, and catalog surfaces after implementation stabilizes.
- [x] Run docs stewardship after skill/docs surfaces change.

## Batch 1 Verification

- [x] `uv run pytest tests/test_nerdbot_schema_contracts.py tests/test_nerdbot_contract_helpers.py tests/test_nerdbot_scripts.py -q`
- [x] `uv run ruff check skills/nerdbot tests/test_nerdbot*.py`
- [x] `uv run wagents openspec validate`
- [x] `git diff --check`
