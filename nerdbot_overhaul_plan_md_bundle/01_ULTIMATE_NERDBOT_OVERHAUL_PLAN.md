# Ultimate Nerdbot Overhaul Plan

> Goal: transform `skills/nerdbot` into an all-inclusive, local-first, OSS-only, Obsidian-compatible LLM-wiki knowledge system that internalizes the best logic from the LLM-wiki ecosystem while preserving Nerdbot’s existing safety, provenance, and migration discipline.

## 0. Decision summary

<details open>
<summary><strong>Open this first: the target product</strong></summary>

Nerdbot should become a **plugin-style skill suite plus Typer CLI** that can create, ingest, compile, query, search, lint, graph, autoresearch, review, watch, and migrate durable markdown knowledge vaults.

The target shape is:

```text
skills/nerdbot/
  SKILL.md                         # top-level router/orchestrator skill
  pyproject.toml                   # package metadata, CLI entrypoint, dependency extras
  AGENTS.md                        # repo-local implementation guidance for coding agents
  README.md                        # human docs for the skill package
  src/nerdbot/
    cli.py                         # Typer app and command registration
    app.py                         # application service container
    config.py                      # Pydantic Settings + TOML loading
    models/                        # Pydantic v2 contracts
    fs.py                          # safe filesystem, path, git, lock helpers
    logging.py                     # Loguru setup
    provenance.py                  # citation anchors, source spans, claim traces
    ingest/                        # native ingest pipeline + adapters
    compiler/                      # native wiki compiler and page updater
    retrieval/                     # native BM25 + semantic + graph + temporal fusion
    graph/                         # native typed graph extraction/export/render
    review/                        # approval queue, patch manifests, safe apply
    research/                      # OSS/free autoresearch loop and source acquisition
    vault/                         # Obsidian compatibility and vault operations
    audit/                         # inventory/lint/migration checks, ported from scripts
    evals/                         # executable eval harness helpers
    interfaces/                    # optional REST/MCP wrappers around services only
  skills/                          # internal coordinated agent skills, not external deps
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
```

The primary command should be `nerdbot`, implemented with Typer. Optional REST/MCP adapters can exist, but they must be thin wrappers over the same service layer and must not become the architecture’s center of gravity.

</details>

<details>
<summary><strong>OSS-only dependency policy</strong></summary>

Nerdbot may use fully OSS/free libraries and local data formats. It must not call or require proprietary LLM-wiki tools, paid search APIs, closed SaaS, or vendor-managed services.

Allowed as first-class ingestion engines:

- **Docling**: default broad-document ingestion adapter. It is MIT-licensed and parses many formats, including PDF, DOCX, PPTX, XLSX, HTML, Markdown, images, audio, WebVTT, LaTeX, and plain text, with advanced PDF layout, reading order, table structure, formulas, OCR, and local execution.
- **OpenDataLoader PDF**: PDF-specialist adapter/fallback for high-fidelity PDF extraction, bounding boxes, tagged-PDF structure, deterministic local parsing, table extraction, AI-safety filtering, and Apache-2.0 licensing.

Allowed optional OSS/free libraries, if useful and license-compatible:

- Typer, Pydantic v2, Pydantic Settings, Loguru, Rich, tqdm, Tenacity, httpx, BeautifulSoup/readability, watchfiles/watchdog, pytest, Ruff, ty.
- SQLite/FTS5 for BM25-style lexical retrieval and durable local state.
- LanceDB OSS or sqlite-vec as optional local semantic-vector storage.
- NetworkX and a small HTML renderer such as vis.js/sigma.js assets for graph export.
- FastAPI only as an optional REST wrapper, not the core operator interface.
- FastMCP or official MCP SDK only as an optional adapter if the final implementation team chooses to expose Nerdbot to MCP clients.

Explicitly do **not** vendor, import, shell out to, or require OpenKB, PageIndex, qmd, engraph, graphify, Understand-Anything, llm-wiki-agent, llm-wiki-compiler, nashsu/llm_wiki, claude-obsidian, karpathy-llm-wiki, SwarmVault, Tavily, proprietary PDF APIs, or cloud vector databases. Use them as design references only.

</details>

## 1. Baseline assessment of uploaded Nerdbot

<details open>
<summary><strong>What Nerdbot already does well</strong></summary>

The current uploaded skill already has several important strengths:

1. **Clear domain boundary** — it is not generic notes, not docs-site generation, and not database-backed KB design. It is specifically for git-friendly, Obsidian-native, persistent KBs.
2. **Strong vocabulary** — `raw`, `wiki`, `schema`, `config`, `indexes`, `activity log`, `provenance`, `canonical material`, `derived output`, `imperfect repo`, `migration`, `vault`, `shared vault config`, and `Dataview metadata` are already explicitly defined.
3. **Safe operating gates** — classify, inventory, plan, confirm, execute, verify, handoff.
4. **Obsidian-first orientation** — supports `[[wikilinks]]`, aliases, frontmatter, shared `.obsidian/` surfaces, and vault migration safety.
5. **Existing scripts** — `kb_bootstrap.py`, `kb_inventory.py`, and `kb_lint.py` are concrete, useful, and should be ported into package modules instead of discarded.
6. **Existing evals** — the skill already has behavioral eval fixtures for multiple modes and negative controls.

</details>

<details>
<summary><strong>What the upload lacks relative to the LLM-wiki ecosystem</strong></summary>

Nerdbot is currently more of a skill contract plus helper scripts than a complete knowledge system. The missing product surfaces are:

- No packaged `nerdbot` CLI entrypoint.
- No durable operation state beyond activity-log conventions.
- No ingestion engine that converts arbitrary document types into normalized fragments with citation anchors.
- No compile pipeline that turns normalized sources into source summaries, entities, concepts, syntheses, questions, comparisons, hot cache, and index updates.
- No incremental source hashing or pending-change detection.
- No approval/review queue for risky updates, contradictions, merges, renames, or ambiguous facts.
- No local hybrid retrieval implementation.
- No typed graph model, graph exports, or graph-derived gap/cluster insight logic.
- No autoresearch loop.
- No watch mode for raw inboxes or vault edits.
- No Obsidian canvas/dashboard generation beyond template conventions.
- No evaluation harness for answer grounding, citation fidelity, graph integrity, ingest idempotence, or vault lint quality.
- No installable package metadata, lockfile strategy, typed tests, docs, or reproducible dev environment.

</details>

<details>
<summary><strong>Observed lint/inventory implications from the uploaded archive</strong></summary>

Running Nerdbot’s own inventory/lint scripts against the uploaded skill archive indicates the current skill root is not itself a scaffolded KB root. It has `SKILL.md`, `references/`, `assets/`, `scripts/`, and `evals/`, but not a canonical `raw/`, `wiki/`, `schema/`, `config/`, `indexes/`, or `activity/` tree. That is acceptable for a skill package, but the overhaul should distinguish:

1. **Skill package layout** — the installed tool/skill itself.
2. **Managed vault layout** — the user’s KB/vault that Nerdbot creates or improves.
3. **Generated state layout** — derived indexes, graphs, caches, review queues, and search stores.

The current lint also treats example wikilinks such as `[[wikilinks]]`, placeholder paths, and template links as broken. The rewrite should add template-aware lint suppression or template placeholder syntax so examples do not look like production link failures.

</details>

## 2. Ecosystem feature internalization map

<details open>
<summary><strong>Feature map: what to implement natively inside Nerdbot</strong></summary>

| Ecosystem inspiration | Useful logic to internalize | Nerdbot-native module | Direct dependency? |
|---|---|---:|---:|
| Karpathy LLM Wiki pattern | raw/wiki/schema separation; ingest/query/lint; persistent compounding markdown; index/log; LLM-maintained wiki | `compiler`, `audit`, `vault`, `models` | No |
| OpenKB | long-doc-aware ingestion; compile raw docs into wiki; chat/save explorations; no-vector-db-first retrieval posture | `ingest`, `compiler`, `query` | No |
| PageIndex | hierarchical long-doc reasoning idea; tree/path-aware source navigation | `ingest.structure`, `retrieval.longdoc` | No |
| llm-wiki-agent | entities, concepts, source summaries, living overview, syntheses, graph JSON/HTML, contradiction flags | `compiler`, `graph`, `audit` | No |
| llm-wiki-compiler | incremental compile, source hashes, state, query save-back, MCP resource/tool taxonomy | `state`, `compiler`, `query`, optional `interfaces.mcp` | No |
| claude-obsidian | autoresearch, hot cache, Obsidian vault ergonomics, multi-skill decomposition, linting, setup workflows | `research`, `vault`, `skills/*` | No |
| nashsu/llm_wiki | ingest queue, crash recovery, review system, deep research, graph insights, purpose.md | `queue`, `review`, `research`, `graph`, `vault` | No |
| qmd/engraph | BM25 + semantic + graph expansion + rerank + temporal search; RRF fusion; context bundles; vault health | `retrieval`, `audit`, `context` | No |
| graphify | deterministic extraction first; multimodal graph; topology-based communities; graph HTML/JSON/report export | `graph`, `ingest`, `audit` | No |
| Understand-Anything | interactive graph that teaches; deterministic + inferred relationships; guided tours; graph review | `graph`, `docs`, `evals` | No |
| Docling Graph | Pydantic object extraction, typed relationships, graph exports | `models.graph`, `graph.extract` | No direct dependency required |
| Docling | broad structured document conversion into markdown/JSON/DoclingDocument | `ingest.adapters.docling` | Yes, optional/default |
| OpenDataLoader PDF | PDF-specialist extraction with bounding boxes, reading order, tables, tagged structure, local parsing | `ingest.adapters.opendataloader` | Yes, optional/specialist |
| MarkItDown | lightweight markdown conversion fallback for common formats | `ingest.adapters.markdown_fallback` | Optional only |
| LanceDB | local embedded vector retrieval | `retrieval.semantic` | Optional only |
| MCP | standardized agent tool/resource surface | `interfaces.mcp` | Optional only |

</details>

<details>
<summary><strong>Core principle: implement the system, not wrappers around other systems</strong></summary>

Nerdbot should not become a coordinator that shells out to competing LLM-wiki tools. It should be the system.

Use external projects only to learn patterns:

- **OpenKB/PageIndex** teaches long-document and vectorless-first thinking.
- **qmd/engraph** teaches retrieval-lane design and RRF fusion.
- **graphify/Docling Graph/Understand-Anything** teach typed graph extraction, topology, visualization, and graph-review loops.
- **nashsu/llm_wiki/claude-obsidian** teach review UX, queueing, hot cache, deep research, and Obsidian ergonomics.
- **llm-wiki-compiler** teaches incremental compile state, source hashes, and optional MCP resource design.

But Nerdbot should own every durable schema, every page format, every index format, every graph format, and every CLI command.

</details>

## 3. Target managed-vault layout

<details open>
<summary><strong>Recommended managed KB/vault structure</strong></summary>

```text
<kb-root>/
  .obsidian/
    templates/
      wiki-note-template.md
      source-note-template.md
      synthesis-note-template.md
    snippets/
    # never auto-overwrite volatile workspace files

  raw/
    inbox/                         # drop zone watched by nerdbot
    sources/                       # immutable canonical source files
    captures/                      # URL/article/RSS/HTML captures
    extracts/                      # normalized extraction artifacts
    assets/                        # images, audio, video, figures, attachments

  wiki/
    index.md                       # LLM/agent navigation entrypoint
    hot.md                         # compact recent-context cache, <=500 words
    purpose.md                     # goals, scope, thesis, research questions
    overview.md                    # living synthesis across the whole KB
    sources/                       # one page per source, source summary contract
    concepts/                      # one atomic concept per page
    entities/                      # people/orgs/tools/projects/protocols
    claims/                        # optional atomic claim cards for high-rigor KBs
    syntheses/                     # cross-source analysis and filed query answers
    questions/                     # saved questions and answer provenance
    comparisons/                   # side-by-side evaluations
    workflows/                     # repeatable SOPs learned by the KB
    meta/                          # dashboards, lint reports, graph reports

  schema/
    nerdbot.schema.json            # generated JSON schema bundle
    frontmatter.schema.json
    graph.schema.json
    review.schema.json
    retrieval.schema.json
    migration.schema.json

  config/
    nerdbot.toml
    obsidian-vault.md
    retrieval.toml
    ingestion.toml
    research.toml

  indexes/
    source-map.md
    coverage.md
    manifest.jsonl                 # source/page hashes, timestamps, status
    claims.jsonl
    citations.jsonl
    search.sqlite                  # FTS5/BM25, metadata, chunks
    embeddings.lance/              # optional LanceDB semantic index
    context-bundles/               # generated retrieval bundles

  graph/
    graph.json                     # typed graph nodes/edges
    graph.graphml                  # optional tool-neutral export
    graph.cypher                   # optional import script for graph DBs
    graph.html                     # local interactive visualization
    communities.json
    graph-report.md

  review/
    queue.jsonl                    # pending approvals
    applied.jsonl
    rejected.jsonl
    patches/                       # proposed patch manifests/diffs

  activity/
    log.md                         # append-only human-readable log
    operations.jsonl               # machine-readable operation log

  exports/
    # derived output only; never canonical truth
```

</details>

<details>
<summary><strong>Why add `purpose.md`, `hot.md`, `claims/`, `review/`, and machine-readable logs?</strong></summary>

- `purpose.md` prevents the wiki from becoming a generic pile of notes. It gives the compiler a target objective, scope, exclusions, and evolving thesis.
- `hot.md` is a small recent-context cache so agents do not crawl the entire vault just to recover session context.
- `claims/` is optional, but it is useful for high-rigor domains where each fact needs a stable citation anchor and contradiction state.
- `review/` makes risky or ambiguous changes auditable before they mutate canonical wiki pages.
- `operations.jsonl` lets tests, dashboards, and future interfaces reason over mutation history without scraping prose logs.

</details>

## 4. Architecture blueprint

<details open>
<summary><strong>Core service modules</strong></summary>

```text
nerdbot.app
  - constructs services from config
  - passes filesystem guard, clock, logger, state DB, and policy objects

nerdbot.models
  - Pydantic contracts for Source, Fragment, Citation, Claim, Page, Graph, ReviewItem, Operation
  - emits JSON schemas into schema/

nerdbot.fs
  - root resolution, symlink refusal, path allowlists, file locks, atomic writes, git state checks
  - never writes outside approved KB root

nerdbot.ingest
  - accepts files, directories, URLs, inbox items
  - fingerprints sources
  - dispatches to Docling/OpenDataLoader/plain-text adapters
  - emits normalized fragments with coordinates, headings, tables, images, checksums, and citation anchors

nerdbot.compiler
  - converts normalized source fragments into source summaries, concepts, entities, claims, syntheses, overview, index, hot cache
  - detects contradictions, duplicates, weak claims, stale claims, and missing citations
  - generates patch manifests instead of directly rewriting when risk is nontrivial

nerdbot.retrieval
  - SQLite FTS5 lexical index
  - optional semantic index with LanceDB/local embeddings
  - graph expansion lane
  - temporal lane
  - optional local reranker lane
  - intent classifier and RRF fusion

nerdbot.graph
  - deterministic graph extraction from frontmatter, wikilinks, citations, source metadata, Docling structure, tags, and file paths
  - optional agent-assisted inferred edge generation during compile
  - community detection and graph report
  - exports graph.json/html/graphml/cypher

nerdbot.review
  - queue, list, show, approve, reject, apply, rollback, explain
  - patch manifest model and conflict detection

nerdbot.research
  - free/OSS source discovery and acquisition loops
  - query plans, URL fetch, RSS/sitemap/arXiv/OpenAlex/Crossref adapters where appropriate
  - never requires paid search APIs
  - routes fetched material through ingest and review

nerdbot.vault
  - Obsidian metadata, aliases, wikilinks, templates, snippets, embeds, canvas/dashboard helpers
  - volatile `.obsidian` safety policy

nerdbot.audit
  - ports and improves current `kb_inventory.py`, `kb_lint.py`, and `kb_bootstrap.py`
  - adds graph, retrieval, citation, schema, queue, and eval checks

nerdbot.interfaces
  - optional REST and MCP wrappers
  - CLI remains canonical
```

</details>

<details>
<summary><strong>CLI-first command surface</strong></summary>

Recommended top-level command tree:

```text
nerdbot init [ROOT]
nerdbot status [ROOT]
nerdbot doctor [ROOT]

nerdbot ingest add SOURCE... [--adapter auto|docling|opendataloader|text]
nerdbot ingest convert SOURCE... [--to md,json]
nerdbot ingest queue [ROOT]
nerdbot ingest run [ROOT] [--approve-safe]

nerdbot compile run [ROOT] [--scope changed|all|source|page]
nerdbot compile plan [ROOT]
nerdbot compile hot [ROOT]
nerdbot compile index [ROOT]

nerdbot query ask QUESTION [--budget N] [--save]
nerdbot search QUERY [--explain] [--lane bm25|semantic|graph|temporal|all]
nerdbot context topic TOPIC [--budget N]
nerdbot context page PAGE [--neighbors N]

nerdbot graph build [ROOT]
nerdbot graph render [ROOT]
nerdbot graph inspect NODE
nerdbot graph communities [ROOT]
nerdbot graph gaps [ROOT]

nerdbot review list [ROOT]
nerdbot review show ITEM_ID
nerdbot review approve ITEM_ID
nerdbot review reject ITEM_ID
nerdbot review apply [ROOT] [--approved-only]

nerdbot research plan TOPIC
nerdbot research fetch PLAN_OR_QUERY
nerdbot research run TOPIC [--rounds N] [--max-sources N]
nerdbot research ingest [ROOT]

nerdbot audit inventory [ROOT]
nerdbot audit lint [ROOT] [--fail-on warning|critical|none]
nerdbot audit provenance [ROOT]
nerdbot audit links [ROOT]
nerdbot audit graph [ROOT]
nerdbot audit retrieval [ROOT]

nerdbot vault normalize [ROOT] [--plan-only]
nerdbot vault templates [ROOT]
nerdbot vault canvas [ROOT]
nerdbot migrate plan [ROOT]
nerdbot migrate apply PLAN_ID

nerdbot watch [ROOT] [--raw-inbox] [--compile-safe]

# optional, not MVP-critical
nerdbot serve rest [ROOT]
nerdbot serve mcp [ROOT]
```

The CLI should expose machine-readable JSON with `--json` for every command that has structured output.

</details>

<details>
<summary><strong>Optional REST/MCP posture</strong></summary>

Do not start with MCP as the implementation core. A great Typer CLI plus reusable service layer is sufficient for local-first operation and easier to test.

Add optional interfaces only after core modules are stable:

- **REST** for browser dashboards, Obsidian plugin integrations, or custom local tools.
- **MCP** for AI clients that need direct tool/resource access.

Both wrappers must call the same application services as the CLI. They must not bypass path safety, approval queues, provenance checks, or operation logging.

</details>

## 5. Ingestion strategy

<details open>
<summary><strong>Default recommendation: Docling-first, OpenDataLoader PDF specialist fallback</strong></summary>

Use **Docling as the default ingestion engine** because it covers the widest range of document types and produces a unified structured representation. Use **OpenDataLoader PDF** as a PDF-specialist adapter when PDF coordinate fidelity, deterministic local parsing, table/bounding-box quality, tagged-PDF structure, or PDF safety filtering is more important than broad format coverage.

Recommended adapter selection:

| Input | Default adapter | Fallback/specialist | Notes |
|---|---|---|---|
| PDF, native text | Docling | OpenDataLoader PDF | Prefer OpenDataLoader when bounding boxes/citation coordinates are critical. |
| PDF, scanned/OCR-heavy | Docling with OCR | OpenDataLoader hybrid/OCR if available locally | Capture OCR confidence and page coordinates. |
| DOCX/PPTX/XLSX/HTML/Markdown/images/audio/WebVTT/LaTeX/plain text | Docling | text/HTML fallback | Keep original and normalized output. |
| URL/article/RSS/HTML capture | HTTP fetch + readability + Docling/HTML adapter | text fallback | Store capture metadata and fetch timestamp. |
| Existing markdown vault notes | native markdown parser | Docling only if needed | Preserve frontmatter and wikilinks. |
| Huge binary source > configured limit | pointer/stub + optional extraction | explicit approval to vendor | Avoid bloating git. |

</details>

<details>
<summary><strong>Normalized source object contract</strong></summary>

Every source conversion should output:

```yaml
source_id: sha256:<hash>
kind: pdf|docx|pptx|xlsx|html|markdown|image|audio|video|url|text|unknown
original_path: raw/sources/...
normalized_paths:
  markdown: raw/extracts/<source_id>.md
  json: raw/extracts/<source_id>.json
  assets: raw/assets/<source_id>/
adapter:
  name: docling|opendataloader|native-markdown|text
  version: ...
fingerprint:
  sha256: ...
  size_bytes: ...
  mtime_utc: ...
fragments:
  - fragment_id: sha256:<source_hash>:p3:b12
    text: ...
    page: 3
    block_type: paragraph|heading|table|figure|caption|list|code|quote|audio_segment
    heading_path: [Section, Subsection]
    bbox: {page: 3, x0: 0.1, y0: 0.2, x1: 0.9, y1: 0.27}
    char_span: [1200, 1540]
    citation_anchor: raw/extracts/<source_id>.json#fragment=<fragment_id>
warnings:
  - hidden_text_removed
  - low_ocr_confidence
  - unsupported_formula
```

All wiki claims should cite these anchors rather than vague “from source X” references.

</details>

<details>
<summary><strong>Ingestion quality gates</strong></summary>

Ingestion is not complete until Nerdbot can answer:

1. Was the original preserved or explicitly pointer-stubbed?
2. Which adapter converted it, and what version?
3. Were tables, figures, equations, and page coordinates preserved where possible?
4. Does every normalized fragment have a stable source hash and citation anchor?
5. Are prompt-injection-like hidden or invisible text artifacts flagged?
6. Can the source be re-converted idempotently?
7. Did the operation update `indexes/manifest.jsonl`, `indexes/source-map.md`, and `activity/log.md`?

</details>

## 6. Native compiler design

<details open>
<summary><strong>Compile pipeline phases</strong></summary>

```text
raw source(s)
  -> normalize source fragments
  -> source summary page
  -> candidate entities/concepts/claims
  -> retrieve existing related pages
  -> plan page updates
  -> detect contradictions/duplicates/gaps
  -> create patch manifest
  -> auto-apply safe changes OR queue risky changes
  -> update index/source-map/coverage/hot/log/graph/search
```

The compiler should be incremental and hash-aware:

- If source hash unchanged, skip reconversion unless forced.
- If normalized fragments unchanged, skip page updates unless schema changed.
- If a page would be renamed, merged, deleted, or heavily rewritten, enqueue review.
- If the source contradicts existing claims, create `review` items and contradiction edges rather than silently rewriting.

</details>

<details>
<summary><strong>Page taxonomy</strong></summary>

| Page type | Directory | Rule |
|---|---|---|
| Source summary | `wiki/sources/` | One per canonical source. Must cite raw source and extraction artifacts. |
| Concept | `wiki/concepts/` | One atomic idea/framework/method. Update rather than duplicate. |
| Entity | `wiki/entities/` | Person/org/tool/project/protocol. Include aliases. |
| Claim | `wiki/claims/` | Optional high-rigor atomic claim card with status and citations. |
| Synthesis | `wiki/syntheses/` | Cross-source analysis or saved answer. |
| Question | `wiki/questions/` | Filed query + answer provenance. |
| Comparison | `wiki/comparisons/` | Side-by-side evaluation. |
| Workflow/SOP | `wiki/workflows/` | Repeatable process learned by the KB. |
| Meta | `wiki/meta/` | Dashboards, lint reports, graph reports. |

</details>

<details>
<summary><strong>Frontmatter contract</strong></summary>

Every wiki page should have YAML frontmatter like:

```yaml
title: "Readable Title"
slug: readable-title
kind: concept|entity|source|claim|synthesis|question|comparison|workflow|meta
status: draft|active|needs-review|deprecated|archived
created: 2026-04-30T00:00:00Z
updated: 2026-04-30T00:00:00Z
aliases: []
tags: []
sources: []
source_count: 0
claim_count: 0
confidence: high|medium|low|unknown
review_status: auto-applied|pending|approved|rejected|manual
provenance_required: true
nerdbot_schema_version: "1.0.0"
```

Page body sections should be structured by kind, but every substantive claim must cite source anchors or declared canonical material.

</details>

<details>
<summary><strong>Review-triggering compiler events</strong></summary>

Queue review instead of auto-applying when any of these happen:

- New source contradicts an active claim.
- Page merge/split/rename/delete is proposed.
- Source summary confidence is low or OCR confidence is poor.
- Claim lacks precise citation anchors.
- Operation would affect more than a configured file threshold.
- A user-authored canonical page would be touched.
- Frontmatter schema migration is needed.
- Graph community/gap analysis suggests non-obvious restructuring.
- Research loop proposes external sources with uncertain quality.

</details>

## 7. Native hybrid retrieval design

<details open>
<summary><strong>Retrieval lanes</strong></summary>

Implement qmd/engraph-style logic natively, not by calling qmd/engraph.

1. **Lexical lane** — SQLite FTS5/BM25 over page text, headings, aliases, tags, source summaries, and fragments.
2. **Semantic lane** — optional local embeddings stored in LanceDB OSS or sqlite-vec. Disabled by default if no local embedding model is configured.
3. **Graph lane** — expand through wikilinks, citation edges, entity/concept co-occurrence, source overlap, contradiction/support edges, community membership, and `same_as` aliases.
4. **Temporal lane** — boost recent updates, date-specific pages, source dates, frontmatter timestamps, and “last week/month/recent” queries.
5. **Rerank lane** — optional local cross-encoder or heuristic reranker. No cloud dependency.

Fuse lanes with Reciprocal Rank Fusion (RRF). Add `--explain` output showing lane scores, final rank, and provenance.

</details>

<details>
<summary><strong>Query flow</strong></summary>

```text
question
  -> classify intent: lookup|conceptual|temporal|source-verification|gap-analysis|navigation|migration
  -> generate search plan and lane weights
  -> retrieve candidate pages/fragments
  -> graph-expand if useful
  -> rerank and budget context
  -> answer from wiki/indexes first
  -> verify citations against raw/extracts when needed
  -> state confidence, gaps, and proposed enrich/research tasks
  -> optionally save answer as wiki/questions or wiki/syntheses after approval
```

Query remains read-only unless `--save` or explicit mutation approval is provided.

</details>

<details>
<summary><strong>Context bundle contract</strong></summary>

A context bundle should be a reproducible artifact:

```yaml
bundle_id: ctx_<hash>
query: "..."
created: "..."
budget_tokens: 8000
strategy: rrf-hybrid-v1
items:
  - path: wiki/concepts/example.md
    score: 0.93
    lanes: {bm25: 0.7, semantic: 0.8, graph: 0.4, temporal: 0.1}
    excerpts:
      - heading: "Evidence"
        text: "..."
        citations: [raw/extracts/source.json#fragment=...]
```

</details>

## 8. Native graph system

<details open>
<summary><strong>Typed graph schema</strong></summary>

Nodes:

- `vault`, `page`, `source`, `fragment`, `claim`, `concept`, `entity`, `question`, `synthesis`, `tag`, `attachment`, `operation`, `review_item`, `community`.

Edges:

- `links_to`, `cites`, `supports`, `contradicts`, `mentions`, `defines`, `derived_from`, `updates`, `supersedes`, `same_as`, `related_to`, `co_occurs`, `belongs_to`, `answered_by`, `needs_review`, `created_by_operation`, `rendered_from`.

Every edge should include:

```yaml
edge_id: sha256:<source>:<relation>:<target>
source: node_id
target: node_id
relation: cites|supports|contradicts|...
confidence: 0.0-1.0
origin: deterministic|compiler|reviewed|inferred
provenance: []
created: ...
updated: ...
```

</details>

<details>
<summary><strong>Graph extraction passes</strong></summary>

1. **Deterministic file pass** — paths, page types, frontmatter, tags, aliases, wikilinks, markdown links, embeds, source references.
2. **Source-structure pass** — Docling/OpenDataLoader headings, tables, figures, pages, bounding boxes, captions, and structure tags.
3. **Citation/claim pass** — claims and citation anchors from compiler output.
4. **Similarity/co-occurrence pass** — source overlap, shared tags, shared entities, direct co-mentions.
5. **Inferred relationship pass** — agent-assisted or heuristic inferred edges, always marked `origin: inferred` and lower confidence until reviewed.
6. **Community pass** — topology-based clustering, graph gaps, bridge nodes, orphan pages, dense communities, and surprising weak ties.
7. **Render/export pass** — `graph.json`, `graph.html`, `graph.graphml`, optional `graph.cypher`, and `wiki/meta/graph-report.md`.

</details>

<details>
<summary><strong>Graph insights to expose</strong></summary>

- Orphan pages and orphan sources.
- High-degree hub concepts.
- Bridge nodes between communities.
- Contradiction clusters.
- Claims with too few citations.
- Concepts with many sources but no synthesis.
- Entities with inconsistent aliases.
- Stale pages relative to recently ingested sources.
- Research gaps: communities with unanswered questions or low evidence density.
- Suggested merges/splits, always queued for review.

</details>

## 9. Autoresearch system

<details open>
<summary><strong>Free/OSS autoresearch stance</strong></summary>

Autoresearch must not require paid APIs such as Tavily. Use only free/OSS/local mechanisms by default:

- User-supplied URLs.
- RSS/Atom feeds.
- Sitemaps.
- Direct HTTP fetching with `httpx`.
- Open academic APIs where appropriate, such as arXiv, Crossref, OpenAlex, PubMed/NCBI, semantic-scholar-like APIs only when free and allowed by terms.
- Local browser/bookmark/clipping inbox if present.
- Agent-provided web results when the execution environment has browsing, but the codebase should not assume that capability.

</details>

<details>
<summary><strong>Autoresearch loop</strong></summary>

```text
research plan TOPIC
  -> read purpose.md, coverage.md, graph gaps, recent questions
  -> generate research questions and source constraints
  -> build source acquisition plan
  -> fetch candidate sources from free/open/user-supplied surfaces
  -> score source quality: primary/official/peer-reviewed/recency/relevance
  -> queue candidates for review if uncertain
  -> ingest approved sources
  -> compile source summaries and affected pages
  -> update graph, hot cache, coverage, and log
  -> emit research report with gaps and next queries
```

Autoresearch should maintain a `research.toml` program and `wiki/meta/research-report.md`, but the code must be conservative: no uncontrolled crawling, no credential scraping, no bypassing robots/terms, and no hidden cloud calls.

</details>

## 10. Review queue and patch manifests

<details open>
<summary><strong>Patch manifest structure</strong></summary>

Every nontrivial operation should generate a patch manifest before writing:

```yaml
patch_id: patch_<hash>
operation: ingest|compile|research|graph|vault-normalize|migration
risk: low|medium|high|destructive
created: ...
inputs: []
files:
  - path: wiki/concepts/example.md
    action: create|update|rename|delete
    before_hash: null
    after_hash: sha256:...
    summary: "Create concept page from source X"
claims_added: []
claims_changed: []
links_added: []
review_items: []
rollback:
  strategy: git-revert|restore-before-content|manual
```

Low-risk patches can auto-apply only if policy allows. Medium/high-risk patches must wait in `review/queue.jsonl`.

</details>

<details>
<summary><strong>Review commands</strong></summary>

```text
nerdbot review list --risk high
nerdbot review show <item-id>
nerdbot review approve <item-id> --note "verified against source"
nerdbot review reject <item-id> --reason "duplicate page"
nerdbot review apply --approved-only
nerdbot review explain <item-id>
```

Review decisions should update `review/applied.jsonl` or `review/rejected.jsonl` and append a human-readable summary to `activity/log.md`.

</details>

## 11. Obsidian compatibility

<details open>
<summary><strong>Obsidian rules</strong></summary>

Nerdbot-managed wiki pages should be easy to use inside Obsidian:

- Prefer `[[Page Title]]` or `[[page-slug|Alias]]` internal links.
- Preserve frontmatter on edits.
- Maintain `aliases`, `tags`, `kind`, `status`, `updated`, and `source_count` fields consistently.
- Keep filenames stable where possible.
- Store attachments under `raw/assets/` or a configured attachment directory.
- Generate templates under `.obsidian/templates/`.
- Do not rewrite volatile `.obsidian/workspace*.json`, graph state, hotkeys, or personal UI state by default.
- Add optional `.canvas` generation for graph/community overview only after the JSON graph is stable.

</details>

<details>
<summary><strong>Vault dashboards</strong></summary>

Generate simple markdown dashboards that work without proprietary plugins:

- `wiki/meta/dashboard.md`
- `wiki/meta/review.md`
- `wiki/meta/coverage.md`
- `wiki/meta/graph-report.md`
- `wiki/meta/research-report.md`

If Dataview or Obsidian Bases are present, optionally provide compatible snippets, but do not make the vault depend on them.

</details>

## 12. Testing and evaluation strategy

<details open>
<summary><strong>Test classes</strong></summary>

| Test class | Examples |
|---|---|
| Unit | Pydantic schema validation, path guards, slugging, frontmatter parser, RRF fusion, graph edge extraction |
| Golden fixtures | Ingest PDF/HTML/Markdown fixture; compare normalized fragments and citations |
| Idempotence | Re-run ingest/compile with unchanged source; no duplicate pages or unstable hashes |
| Safety | Symlink traversal, writes outside root, destructive migration without approval, hidden PDF text flags |
| Retrieval | BM25 query, graph expansion, temporal query, RRF explain output |
| Graph | No dangling nodes, valid edge relation enum, community export, graph HTML generation |
| Obsidian | Wikilink resolution, aliases, embeds, frontmatter preservation, template placeholder suppression |
| Review | Risk classification, queue persistence, approve/reject/apply, rollback manifest |
| Autoresearch | Plan generation, fetch metadata, quality scoring, no paid API dependency, source-review queue |
| Skill behavior | Existing eval JSONs updated for new CLI/skill split and negative controls |

</details>

<details>
<summary><strong>Quality gates</strong></summary>

Before the overhaul is complete:

```bash
uv sync --all-extras
uv run ruff check .
uv run ruff format --check .
uv run ty check .
uv run pytest -q
uv run nerdbot doctor tests/fixtures/minimal-vault
uv run nerdbot audit lint tests/fixtures/minimal-vault --fail-on warning
uv run nerdbot ingest add tests/fixtures/sources --root /tmp/nerdbot-fixture --dry-run
uv run nerdbot graph build /tmp/nerdbot-fixture --validate
```

</details>

## 13. Documentation and skill redesign

<details open>
<summary><strong>What to update</strong></summary>

Update every supporting doc so the skill and package agree:

- Rewrite top-level `SKILL.md` as a router into internal modules and CLI workflows.
- Add internal `skills/*/SKILL.md` files for ingest, compile, query, graph, research, review, vault, and audit.
- Update `references/kb-architecture.md` to include the expanded artifact model.
- Update `references/kb-operations.md` to include queues, compilation, retrieval, graph, and autoresearch.
- Update `references/obsidian-vaults.md` for dashboards, templates, aliases, attachments, and canvas.
- Update `references/audit-checklist.md` for retrieval, graph, review, schema, citation, and ingestion checks.
- Update `references/page-templates.md` with source/concept/entity/claim/synthesis/question/comparison/workflow/meta templates.
- Update `references/migration-playbooks.md` with package migration and vault migration paths.
- Add `references/oss-dependencies.md` and `references/ingestion-adapters.md`.
- Add `README.md`, `AGENTS.md`, and `pyproject.toml`.
- Expand `evals/` for new workflows and regression tests.

</details>

## 14. Rollout sequence

<details open>
<summary><strong>Milestone plan</strong></summary>

### M0 — Preserve and package

- Add `pyproject.toml` and `src/nerdbot`.
- Port current scripts into modules with CLI wrappers.
- Add tests proving no regressions in bootstrap/inventory/lint behavior.
- Add `.gitignore` for `.DS_Store`, `__pycache__`, generated state, and caches.

### M1 — Schema and CLI core

- Add Pydantic models and JSON schema generation.
- Implement Typer command tree.
- Add config loading from `config/nerdbot.toml`.
- Add safe filesystem, atomic writes, path guards, and operation logging.

### M2 — Ingestion

- Implement Docling adapter.
- Implement OpenDataLoader PDF adapter.
- Implement native markdown/text/HTML fallback.
- Emit normalized fragments, citation anchors, source manifests, and source-map updates.

### M3 — Compiler and review queue

- Implement source summaries, entity/concept/claim extraction, page updates, index/coverage/hot/log.
- Implement patch manifests and review queue.
- Add contradiction and duplicate detection.

### M4 — Retrieval

- Implement SQLite FTS5/BM25 index.
- Implement RRF fusion and `--explain`.
- Add graph and temporal lanes.
- Add optional semantic lane.

### M5 — Graph

- Implement typed graph extraction, validation, community detection, and graph reports.
- Render local `graph.html`.
- Add Obsidian dashboard/canvas helpers.

### M6 — Autoresearch and watch mode

- Implement research plans, free source fetching, source scoring, queueing, ingest handoff.
- Implement `watch` over raw inbox and config-driven safe compile behavior.

### M7 — Optional interfaces

- Add REST wrapper if needed.
- Add MCP wrapper if needed.
- Verify wrappers do not bypass CLI/service safety.

### M8 — Docs, evals, hardening

- Update all references, assets, skill docs, eval fixtures.
- Add fixtures and end-to-end tests.
- Add security checks, reproducible packaging, and release checklist.

</details>

## 15. Source notes used for this plan

<details>
<summary><strong>Primary public sources consulted</strong></summary>

- Docling docs and repository: <https://docling-project.github.io/docling/> and <https://github.com/docling-project/docling>
- OpenDataLoader PDF docs and repository: <https://opendataloader.org/docs> and <https://github.com/opendataloader-project/opendataloader-pdf>
- Docling Graph repository: <https://github.com/IBM/docling-graph>
- Typer repository/docs: <https://github.com/fastapi/typer> and <https://typer.tiangolo.com/>
- MarkItDown repository: <https://github.com/microsoft/markitdown>
- LanceDB docs/repository: <https://docs.lancedb.com/> and <https://github.com/lancedb/lancedb>
- MCP organization/spec docs: <https://github.com/modelcontextprotocol> and <https://modelcontextprotocol.io/>
- OpenKB: <https://github.com/VectifyAI/OpenKB>
- PageIndex: <https://github.com/VectifyAI/PageIndex>
- llm-wiki-agent: <https://github.com/SamurAIGPT/llm-wiki-agent>
- llm-wiki-compiler: <https://github.com/atomicmemory/llm-wiki-compiler>
- claude-obsidian: <https://github.com/AgriciDaniel/claude-obsidian>
- nashsu/llm_wiki: <https://github.com/nashsu/llm_wiki>
- engraph: <https://github.com/devwhodevs/engraph>
- graphify: <https://github.com/safishamsi/graphify>
- Understand-Anything: <https://github.com/Lum1104/Understand-Anything>

</details>
