# Schema Contracts

## Baseline Entities

| Entity | Required identity | Notes |
|--------|-------------------|-------|
| Source | stable source ID, raw path, checksum when available | Originals remain in `raw/` or are represented by pointer stubs |
| Extract | source ID, extract path, parser/adapter, timestamp | Never replaces original source |
| Wiki page | path, title, kind, status, updated, source count | Claims require provenance |
| Claim | claim text, source reference, evidence type, notes | Can point to `raw`, canonical material, or a vault note |
| Review item | item ID, mode, target, risk, proposed action, status | Save-back queue for query gaps and watch events |
| Activity entry | timestamp, mode, summary, layer changes, risk/rollback, follow-up | Append-only |

## Public Contract Modules

| Module | Contract | Notes |
|--------|----------|-------|
| `nerdbot.sources` | Source records, source IDs, checksums, raw paths, pointer stubs | Pure helpers; no filesystem mutation |
| `nerdbot.evidence` | Claim records, review items, freshness classes, review statuses, confidence caps | Claims default to review-visible until approved |
| `nerdbot.operations` | Operation journal entries and stable operation IDs | JSONL-friendly append records |
| `nerdbot.retrieval` | Query result payloads from `wiki/` and `indexes/` | Read-only lexical baseline; semantic reranking remains optional |
| `nerdbot.graph` | Rebuildable graph edges | Derived output, never canonical truth |
| `nerdbot.watch` | Watch event decisions | Queue, ignore, wait, or classify; never rewrite directly |
| `nerdbot.replay` | Dry-run replay results | Preserve failed attempts and surface review-needed gaps |
| `nerdbot.research` | Research journal entries and approved-ingest policy | Journal-only is the safe default |

## Source Record Fields

`source_id`, `original_location`, `raw_path`, `capture_method`, `captured_at`, `size_bytes`, `checksum`, `license_or_access_notes`, and `intended_wiki_coverage` are the required source-record keys. Source-summary and source-note templates may include a human-friendly source-record subset, but they must also include the full machine source-record block. If an original cannot be copied into `raw/`, create a pointer stub rather than dropping provenance.

## Evidence Ledger Fields

`claim_id`, `claim`, `wiki_path`, `source_id`, `evidence_path`, `evidence_type`, `freshness_class`, `review_status`, `confidence`, `updated`, and `notes` are the required claim keys. Freshness classes are `static`, `slow`, `medium`, `fast`, and `unknown`; review statuses are `pending`, `approved`, `applied`, `rejected`, `blocked`, and `superseded`.

## Generated Artifacts

Generated retrieval and graph artifacts live under `indexes/generated/`. Watch checkpoints live under `activity/checkpoints/`. These artifacts are rebuildable and must never become the only copy of a source, claim, or activity record.

## Minimum Frontmatter

Use the Obsidian-compatible fields already defined in `kb-architecture.md` unless a KB has a stronger local convention: `title`, `tags`, `aliases`, `kind`, `status`, `updated`, `source_count`, and optional `cssclasses`.

## Drift Rule

If a schema field appears in a starter template, reference doc, CLI payload, or eval, update the corresponding contract test in the same batch.
