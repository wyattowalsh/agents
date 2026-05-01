# Ingestion Adapters

## Currently Implemented

The current package implements source-record, pointer-stub, local-file, and inline-text ingest planning in `nerdbot.sources` and keeps ingest dependency-light. `nerdbot ingest --apply` writes planned captures under `raw/`, appends `indexes/source-map.md`, and records an operation journal entry. Outside-vault local files require `--copy-outside-root` before bytes are copied; secret-looking, symlinked, oversized, and unreadable paths remain pointer stubs. Remote crawling and heavy parsing adapters remain optional extras.

## Adapter Contract

Adapters should preserve originals and produce normalized extracts, summaries, or review items. They must never replace source files.

Required adapter output:

- Source ID
- Adapter name and version when available
- Original raw path or pointer stub
- Extract path
- Extract format
- Confidence or known limitations
- Provenance anchors available for `wiki/` claims

Adapters may emit review items when confidence, license, freshness, or parser warnings prevent direct promotion. They may not rewrite canonical wiki pages as a side effect of ingest.

Adapters must preserve pointer-stub metadata for non-copied sources whenever it can be known safely, including size, checksum, original location, capture method, and access notes.

## Planned Adapter Lanes

- Native markdown and text parser.
- Docling broad deterministic parser.
- Granite Docling live model execution path.
- OpenDataLoader PDF specialist path.
- MarkItDown fallback adapter.

The baseline should keep native Markdown/text parsing dependency-light and treat Docling, OpenDataLoader, MarkItDown, crawl providers, VLM parsing, and semantic enrichment as optional extras.
