# Codex Prompt — Overhaul Nerdbot into a Native LLM-Wiki Knowledge System

Copy this prompt into Codex from the repository root that contains `skills/nerdbot`.

```text
You are Codex working in the `agents` repository. Your task is to transform `skills/nerdbot` from a strong agent skill plus helper scripts into a production-quality, CLI-first, local-first, OSS-only, Obsidian-compatible, LLM-wiki-inspired knowledge orchestration system.

Critical constraints:

1. WAgents is only for agents-repo scope helpers. Do not make WAgents the knowledge system. Nerdbot itself must be the all-inclusive LLM-wiki/vault system.
2. Internalize useful feature logic from the LLM-wiki ecosystem, but do NOT depend on those tools directly. Do not vendor, import, shell out to, or require OpenKB, PageIndex, qmd, engraph, graphify, Understand-Anything, llm-wiki-agent, llm-wiki-compiler, nashsu/llm_wiki, claude-obsidian, karpathy-llm-wiki, SwarmVault, Tavily, or proprietary/cloud services.
3. Allowed first-class external ingestion engines: Docling and OpenDataLoader PDF. MarkItDown may be added only as an optional lightweight fallback adapter behind an explicit extra/config, not as the core ingestion strategy.
4. Keep everything 100% OSS/free and local-first. No paid search APIs, cloud vector databases, proprietary PDF APIs, or required hosted services.
5. Typer CLI is the primary interface. Optional REST/MCP wrappers may be added later, but only as thin adapters over the same service layer and only after the CLI/core services are stable.
6. Preserve Nerdbot’s existing safety model: inventory first, additive repair first, explicit approval before destructive or high-impact changes, raw source immutability, provenance for substantive claims, small reviewable batches, and Obsidian-compatible paths/frontmatter/wikilinks.
7. Do not rewrite user-authored canonical material without explicit approval. Any rename, deletion, merge, split, large rewrite, schema migration, or `.obsidian` shared config change must generate a review item/patch manifest first.
8. Default Python target is 3.13 unless repo constraints require otherwise. Prefer uv, pyproject.toml, Pydantic v2, Pydantic Settings, Typer, Loguru, Rich, tqdm, Tenacity, pytest, Ruff, and ty where appropriate.

Start by inspecting the current `skills/nerdbot` tree. Preserve the existing high-quality docs, safety language, evals, and scripts, but reorganize them into a package-quality implementation.

Current baseline to preserve and improve:

- `SKILL.md` defines Nerdbot as a KB/vault skill with create, ingest, enrich, audit, query, derive, improve, migrate modes.
- `references/` documents KB architecture, operations, audit, migration, Obsidian vaults, and page templates.
- `assets/` provides starter page templates.
- `scripts/kb_bootstrap.py`, `scripts/kb_inventory.py`, and `scripts/kb_lint.py` implement useful bootstrap/inventory/lint behavior.
- `evals/` has behavioral JSON fixtures for existing modes and negative controls.

Target outcome:

Build a native Python package plus coordinated internal agent-skill suite under `skills/nerdbot`:

skills/nerdbot/
  SKILL.md                         # top-level router/orchestrator skill
  README.md                        # human implementation and usage docs
  AGENTS.md                        # implementation guidance for coding agents
  pyproject.toml                   # uv-compatible package metadata and CLI entry point
  src/nerdbot/
    __init__.py
    cli.py                         # Typer app; command groups listed below
    app.py                         # application service container
    config.py                      # Pydantic Settings + config/nerdbot.toml loading
    fs.py                          # safe paths, symlink refusal, file locks, atomic writes
    logging.py                     # Loguru/Rich logging integration
    provenance.py                  # source anchors, citation spans, claim traces
    models/                        # Pydantic v2 contracts
    ingest/                        # native ingestion pipeline + Docling/OpenDataLoader adapters
    compiler/                      # native source->wiki compiler and page updater
    retrieval/                     # native BM25 + graph + temporal + optional semantic fusion
    graph/                         # native typed graph extraction/export/render
    review/                        # approval queue and patch manifests
    research/                      # OSS/free autoresearch loop
    vault/                         # Obsidian compatibility and vault operations
    audit/                         # ported and expanded inventory/lint/bootstrap logic
    query/                         # query planner and answer/context workflows
    interfaces/                    # optional REST/MCP wrappers only
  skills/
    ingest/SKILL.md
    compile/SKILL.md
    query/SKILL.md
    graph/SKILL.md
    research/SKILL.md
    review/SKILL.md
    vault/SKILL.md
    audit/SKILL.md
  references/
  assets/
  evals/
  tests/

Recommended managed KB/vault layout created by `nerdbot init`:

<kb-root>/
  .obsidian/templates/
  .obsidian/snippets/
  raw/inbox/
  raw/sources/
  raw/captures/
  raw/extracts/
  raw/assets/
  wiki/index.md
  wiki/hot.md
  wiki/purpose.md
  wiki/overview.md
  wiki/sources/
  wiki/concepts/
  wiki/entities/
  wiki/claims/
  wiki/syntheses/
  wiki/questions/
  wiki/comparisons/
  wiki/workflows/
  wiki/meta/
  schema/
  config/nerdbot.toml
  config/obsidian-vault.md
  indexes/source-map.md
  indexes/coverage.md
  indexes/manifest.jsonl
  indexes/claims.jsonl
  indexes/citations.jsonl
  indexes/search.sqlite
  indexes/embeddings.lance/              # optional only
  graph/graph.json
  graph/graph.html
  graph/graph.graphml
  graph/communities.json
  graph/graph-report.md
  review/queue.jsonl
  review/applied.jsonl
  review/rejected.jsonl
  review/patches/
  activity/log.md
  activity/operations.jsonl
  exports/

Implementation plan:

Phase 0 — Repository/package foundation

- Add `pyproject.toml` under `skills/nerdbot` with package name such as `nerdbot-skill` or `nerdbot`, a `nerdbot=nerdbot.cli:app` CLI entrypoint, and optional extras:
  - `ingest-docling` for Docling.
  - `ingest-opendataloader` for OpenDataLoader PDF.
  - `semantic` for LanceDB/local embeddings.
  - `rest` for FastAPI.
  - `mcp` for optional MCP SDK/FastMCP.
  - `dev` for pytest/Ruff/ty.
- Create `src/nerdbot` package and migrate current script logic into importable modules.
- Keep `scripts/kb_bootstrap.py`, `scripts/kb_inventory.py`, and `scripts/kb_lint.py` as backwards-compatible wrappers if existing skill docs/evals reference them.
- Add `.gitignore` updates for `.DS_Store`, `__pycache__`, `.pytest_cache`, `.ruff_cache`, generated indexes, local model caches, `indexes/search.sqlite`, `indexes/embeddings.lance/`, and temporary extraction artifacts.
- Add smoke tests that import the package and run `nerdbot --help`.

Phase 1 — Pydantic schema contracts

Implement Pydantic v2 models with explicit version fields and JSON schema export:

- Config models: `NerdbotConfig`, `VaultConfig`, `IngestionConfig`, `RetrievalConfig`, `ResearchConfig`, `ReviewPolicy`, `GraphConfig`.
- Source models: `SourceRecord`, `NormalizedDocument`, `SourceFragment`, `CitationAnchor`, `ExtractionWarning`.
- Wiki models: `WikiPageMeta`, `ClaimRecord`, `PageUpdatePlan`, `PageKind`, `ClaimStatus`, `Confidence`.
- Graph models: `GraphNode`, `GraphEdge`, `KnowledgeGraph`, `NodeKind`, `EdgeRelation`, `GraphCommunity`.
- Review models: `ReviewItem`, `PatchManifest`, `PatchFileChange`, `RiskLevel`, `ReviewDecision`.
- Retrieval models: `RetrievalHit`, `RetrievalBundle`, `SearchExplain`, `LaneScore`, `QueryIntent`.
- Operation models: `OperationRecord`, `ActivityEntry`, `MigrationPlan`.

Add `nerdbot schema export [ROOT]` that writes JSON schema files to `schema/`.

Phase 2 — Safe filesystem, state, and logging

- Implement root resolution with symlink refusal and no writes outside root.
- Implement atomic write helper with before/after hashes.
- Implement file locks for compile/index/write operations.
- Implement operation logging to `activity/operations.jsonl` plus human-readable appends to `activity/log.md`.
- Implement `--dry-run`, `--plan-only`, `--json`, and `--yes` semantics consistently.
- Implement git-aware safeguards: detect dirty worktree before destructive operations, record rollback notes, never force destructive operations without approval.

Phase 3 — Typer CLI

Create a Typer app with command groups:

nerdbot init [ROOT]
nerdbot status [ROOT]
nerdbot doctor [ROOT]
nerdbot schema export [ROOT]

nerdbot ingest add SOURCE... [--root ROOT] [--adapter auto|docling|opendataloader|markdown|text] [--dry-run]
nerdbot ingest convert SOURCE... [--to md,json] [--dry-run]
nerdbot ingest queue [ROOT]
nerdbot ingest run [ROOT] [--approve-safe]

nerdbot compile plan [ROOT]
nerdbot compile run [ROOT] [--scope changed|all|source|page] [--dry-run]
nerdbot compile hot [ROOT]
nerdbot compile index [ROOT]

nerdbot query ask QUESTION [--root ROOT] [--budget N] [--save]
nerdbot search QUERY [--root ROOT] [--explain] [--lane bm25|semantic|graph|temporal|all]
nerdbot context topic TOPIC [--root ROOT] [--budget N]
nerdbot context page PAGE [--root ROOT] [--neighbors N]

nerdbot graph build [ROOT] [--validate]
nerdbot graph render [ROOT]
nerdbot graph inspect NODE [--root ROOT]
nerdbot graph communities [ROOT]
nerdbot graph gaps [ROOT]

nerdbot review list [ROOT]
nerdbot review show ITEM_ID [--root ROOT]
nerdbot review approve ITEM_ID [--root ROOT] [--note TEXT]
nerdbot review reject ITEM_ID [--root ROOT] [--reason TEXT]
nerdbot review apply [ROOT] [--approved-only]
nerdbot review explain ITEM_ID [--root ROOT]

nerdbot research plan TOPIC [--root ROOT]
nerdbot research fetch PLAN_OR_QUERY [--root ROOT]
nerdbot research run TOPIC [--root ROOT] [--rounds N] [--max-sources N]
nerdbot research ingest [ROOT]

nerdbot audit inventory [ROOT]
nerdbot audit lint [ROOT] [--fail-on warning|critical|none] [--include-unlayered]
nerdbot audit provenance [ROOT]
nerdbot audit links [ROOT]
nerdbot audit graph [ROOT]
nerdbot audit retrieval [ROOT]

nerdbot vault normalize [ROOT] [--plan-only]
nerdbot vault templates [ROOT]
nerdbot vault canvas [ROOT]
nerdbot migrate plan [ROOT]
nerdbot migrate apply PLAN_ID [--root ROOT]
nerdbot watch [ROOT] [--raw-inbox] [--compile-safe]

Optional only after core is stable:
nerdbot serve rest [ROOT]
nerdbot serve mcp [ROOT]

Phase 4 — Ingestion adapters

Implement native ingestion pipeline with adapter protocol:

- `can_handle(path_or_url, sniffed_type) -> bool`
- `convert(input, config) -> NormalizedDocument`
- `extract_metadata(input) -> dict`
- `healthcheck() -> AdapterHealth`

Adapters:

1. Docling adapter (default): broad format support, structured JSON/Markdown output, DoclingDocument extraction where available.
2. OpenDataLoader PDF adapter: PDF-specialist output, bounding boxes, reading order, tables, native PDF structure tags where available, safety warnings when available.
3. Native markdown/text adapter: preserve frontmatter, headings, wikilinks, markdown links, local embeds, and raw content.
4. Optional MarkItDown fallback only if explicitly configured.

Every ingested source must produce:

- Original preservation or pointer/stub with reason.
- `SourceRecord` in `indexes/manifest.jsonl`.
- Normalized markdown and JSON under `raw/extracts/`.
- Stable `SourceFragment` records with citation anchors.
- Source-map updates.
- Operation-log and activity-log entries.
- Warnings for low OCR confidence, hidden text, unsupported tables/formulas, or unsafe/ambiguous conversion.

Do not treat ingestion as complete unless fragments have stable IDs and source hashes.

Phase 5 — Native compiler

Implement a native wiki compiler. It must compile normalized sources into durable pages, not merely retrieve chunks at query time.

Compiler responsibilities:

- Create/update `wiki/sources/<source>.md` source summaries.
- Extract candidate concepts, entities, claims, contradictions, comparisons, workflows, and open questions.
- Retrieve existing related pages before writing new ones to avoid duplication.
- Update concept/entity/source/synthesis/question/comparison/workflow pages with frontmatter preservation.
- Update `wiki/index.md`, `wiki/overview.md`, `wiki/hot.md`, `indexes/source-map.md`, `indexes/coverage.md`, `indexes/claims.jsonl`, `indexes/citations.jsonl`, `activity/log.md`, and `activity/operations.jsonl`.
- Generate patch manifests before writes.
- Auto-apply only low-risk changes if policy allows.
- Queue medium/high-risk changes for human review.
- Detect contradictions and create review items/graph edges rather than silently overwriting claims.
- Ensure every substantive claim cites raw/extract anchors or declared canonical material.

Page kinds:

- `source`, `concept`, `entity`, `claim`, `synthesis`, `question`, `comparison`, `workflow`, `meta`.

Frontmatter minimum:

- `title`, `slug`, `kind`, `status`, `created`, `updated`, `aliases`, `tags`, `sources`, `source_count`, `claim_count`, `confidence`, `review_status`, `provenance_required`, `nerdbot_schema_version`.

Phase 6 — Review queue and patch manifests

Implement a review layer inspired by desktop/review-queue patterns but native to Nerdbot.

Queue review for:

- Contradictions.
- Renames, merges, splits, deletes.
- Canonical material rewrites.
- Schema migrations.
- Low-confidence extraction.
- Ambiguous citations.
- Large multi-layer batches.
- Vault normalization that touches aliases/link paths/templates.
- Autoresearch sources with uncertain quality.

Implement:

- `review/queue.jsonl`, `review/applied.jsonl`, `review/rejected.jsonl`, `review/patches/`.
- `nerdbot review list/show/approve/reject/apply/explain`.
- Conflict detection via before hashes.
- Rollback metadata.
- Activity and operation log entries for every review decision.

Phase 7 — Native hybrid retrieval

Implement qmd/engraph-style retrieval logic natively:

Lanes:

1. Lexical lane: SQLite FTS5/BM25 over pages, source summaries, fragments, tags, aliases, and headings.
2. Semantic lane: optional, local-only LanceDB OSS or sqlite-vec with configurable local embedding model. Disabled if not configured.
3. Graph lane: expand through graph edges, source overlap, wikilinks, citations, aliases, community membership, support/contradiction relationships.
4. Temporal lane: use frontmatter dates, source dates, operation dates, filenames, and natural time heuristics for “recent”, “last week”, etc.
5. Rerank lane: optional local-only reranking or heuristic scoring.

Fuse with Reciprocal Rank Fusion. Implement query intent classification and lane-weight adaptation. Implement `--explain` showing lane scores, final score, selected context, and provenance.

Query must answer from `wiki/` and `indexes/` first. It may inspect `raw/`/`raw/extracts` only to verify citations or confirm gaps. Query is read-only unless `--save` or explicit mutation approval is given.

Phase 8 — Native graph system

Implement typed knowledge graph logic inspired by graphify, Docling Graph, and Understand-Anything, but do not call those tools.

Node kinds:

- `vault`, `page`, `source`, `fragment`, `claim`, `concept`, `entity`, `question`, `synthesis`, `tag`, `attachment`, `operation`, `review_item`, `community`.

Edge relations:

- `links_to`, `cites`, `supports`, `contradicts`, `mentions`, `defines`, `derived_from`, `updates`, `supersedes`, `same_as`, `related_to`, `co_occurs`, `belongs_to`, `answered_by`, `needs_review`, `created_by_operation`, `rendered_from`.

Graph passes:

1. Deterministic file pass: paths, page kinds, frontmatter, aliases, tags, wikilinks, markdown links, embeds.
2. Source-structure pass: Docling/OpenDataLoader fragments, headings, tables, pages, figures, coordinates.
3. Claim/citation pass: claims, citations, support/contradiction edges.
4. Co-occurrence/source-overlap pass.
5. Optional inferred relationship pass, always marked `origin: inferred` and lower confidence until reviewed.
6. Community detection pass with OSS graph algorithms.
7. Export/render pass.

Outputs:

- `graph/graph.json`
- `graph/graph.html`
- `graph/graph.graphml`
- optional `graph/graph.cypher`
- `graph/communities.json`
- `wiki/meta/graph-report.md`

Graph insights:

- Orphans, broken graph edges, hub concepts, bridge nodes, contradiction clusters, low-evidence claims, high-source concepts without syntheses, inconsistent aliases, stale pages, research gaps, suggested merges/splits queued for review.

Phase 9 — Autoresearch loop

Implement free/OSS/local-first autoresearch. Do not require paid search APIs.

Default source acquisition options:

- User-supplied URLs.
- RSS/Atom feeds.
- Sitemaps.
- Direct HTTP fetching with `httpx`.
- Open academic APIs where appropriate and terms-compatible: arXiv, Crossref, OpenAlex, PubMed/NCBI.
- Existing raw inbox, browser clippings, local bookmarks, or user-provided files.
- Agent-provided web results only if the runtime supplies them; the code must not assume external browsing.

Autoresearch workflow:

1. Read `wiki/purpose.md`, `wiki/hot.md`, `indexes/coverage.md`, graph gaps, and recent questions.
2. Generate research questions and source constraints.
3. Create source-acquisition plan.
4. Fetch candidate sources conservatively.
5. Score source quality: official/primary, peer-reviewed, recency, relevance, citation/support, license/availability.
6. Queue uncertain sources for review.
7. Ingest approved sources.
8. Compile affected pages.
9. Update graph, hot cache, coverage, and logs.
10. Emit `wiki/meta/research-report.md`.

Phase 10 — Obsidian compatibility and vault UX

Implement vault logic:

- Preserve YAML frontmatter and ordering where practical.
- Generate templates under `.obsidian/templates/`.
- Keep volatile `.obsidian` files out of automated rewrites by default.
- Resolve and lint `[[wikilinks]]`, aliases, embeds, tags, and attachment paths.
- Generate dashboards under `wiki/meta/` that work without Dataview/Bases.
- Optionally generate Obsidian canvas from `graph/graph.json` after graph engine is stable.
- Add `nerdbot vault normalize --plan-only` for mixed markdown repos.
- Preserve path stability and aliases before any rename.

Phase 11 — Watch mode

Implement `nerdbot watch`:

- Watch `raw/inbox/`, `raw/sources/`, and optionally wiki pages.
- Debounce changes.
- Use file locks.
- Convert to ingest queue items.
- Compile only safe/low-risk changes if configured.
- Send ambiguous/risky changes to review queue.
- Log every watcher-triggered operation.

Phase 12 — Optional REST/MCP wrappers

Only implement after CLI and services are stable.

REST:

- FastAPI optional extra.
- Localhost by default.
- API key if exposed beyond localhost.
- Endpoints wrap status/search/query/read/graph/lint/review only.

MCP:

- Optional extra.
- Expose read-only tools first: status, search, query, read page, graph inspect, lint.
- Mutating tools must create review items unless explicitly approved by policy.
- Expose resources such as index, page, graph, state, source manifest.
- Never bypass filesystem safety, patch manifests, or approval queue.

Phase 13 — Docs, internal skills, assets, and evals

Update all supporting docs:

- Rewrite top-level `SKILL.md` as router/orchestrator.
- Add internal skill files for ingest, compile, query, graph, research, review, vault, audit.
- Update `references/kb-architecture.md`, `kb-operations.md`, `obsidian-vaults.md`, `audit-checklist.md`, `migration-playbooks.md`, and `page-templates.md`.
- Add `references/schema-contracts.md`, `references/cli.md`, `references/ingestion-adapters.md`, `references/retrieval.md`, `references/graph.md`, `references/review-queue.md`, `references/autoresearch.md`, `references/testing.md`, and `references/oss-dependencies.md`.
- Update templates for source, concept, entity, claim, synthesis, question, comparison, workflow, meta dashboard, hot cache, purpose page, graph report, review item.
- Update and expand eval JSONs for all new modes.
- Ensure docs state WAgents is separate and Nerdbot is the full LLM-wiki knowledge system.

Phase 14 — Tests and quality gates

Add tests:

- Unit tests for models, config, path guards, slugging, frontmatter, citations, RRF, graph extraction.
- Regression tests for current bootstrap/inventory/lint behavior.
- Golden ingest fixtures for markdown/text and at least one PDF fixture if possible.
- Idempotence tests for repeated ingest/compile.
- Safety tests for symlink traversal, path escape, destructive writes without approval.
- Retrieval tests for lexical, graph, temporal, RRF explain.
- Graph tests for schema validation, no dangling edges, HTML render, community output.
- Review tests for patch manifests, approve/reject/apply, conflicts, rollback metadata.
- Autoresearch tests proving no paid API dependency.
- Obsidian tests for wikilinks, aliases, embeds, frontmatter preservation, volatile `.obsidian` policy.
- CLI tests for `--json`, `--dry-run`, `--plan-only`, and help output.

Quality commands:

uv sync --all-extras
uv run ruff check .
uv run ruff format --check .
uv run ty check .
uv run pytest -q
uv run nerdbot --help
uv run nerdbot doctor tests/fixtures/minimal-vault
uv run nerdbot audit lint tests/fixtures/minimal-vault --fail-on warning

Implementation style:

- Prefer small, typed, composable modules.
- Use Pydantic v2 for durable artifacts and validation.
- Use pathlib, atomic writes, and explicit root guards.
- Use Loguru for logs and Rich for human CLI output.
- Use JSONL for append-only machine-readable records.
- Use markdown files for human-facing state.
- Keep generated indexes/graphs rebuildable.
- Keep raw sources append-only.
- Use deterministic outputs where possible.
- Use review queue when uncertain.
- Preserve existing Nerdbot wording and safety discipline where still valid.

End-state acceptance criteria:

1. `uv run nerdbot init /tmp/example-vault` creates a complete Obsidian-compatible layered vault.
2. `uv run nerdbot ingest add <fixture-source> --root /tmp/example-vault` preserves original source, writes normalized extraction artifacts, updates manifest/source map/log, and creates stable citation anchors.
3. `uv run nerdbot compile run /tmp/example-vault` creates or updates source/concept/entity/index/hot/coverage pages via patch manifests and queues risky changes.
4. `uv run nerdbot search "..." --root /tmp/example-vault --explain --json` returns fused lane scores and provenance.
5. `uv run nerdbot query ask "..." --root /tmp/example-vault --json` answers from wiki/indexes first, verifies raw only when needed, cites sources, states gaps, and does not mutate unless asked.
6. `uv run nerdbot graph build /tmp/example-vault --validate` writes valid `graph/graph.json`, `graph/graph.html`, communities, and report.
7. `uv run nerdbot review list /tmp/example-vault` shows queued contradictions/risky edits; approve/reject/apply flows work and log decisions.
8. `uv run nerdbot research plan "topic" --root /tmp/example-vault --json` produces a source acquisition plan using only free/open/user-provided sources.
9. `uv run nerdbot audit lint /tmp/example-vault --fail-on warning` validates structure, citations, links, graph, retrieval, schema, review queue, and Obsidian compatibility.
10. All docs, assets, skill files, evals, tests, and references are updated to match the new CLI and architecture.

Before making changes, create a concise implementation plan and identify files you will modify. Then implement in dependency order. Prefer partial working milestones over a huge untested rewrite. Do not stop after scaffolding; implement the core service interfaces, CLI, and enough end-to-end behavior/tests to prove the design.
```
