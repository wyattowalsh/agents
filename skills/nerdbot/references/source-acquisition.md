# Source Acquisition

## Currently Implemented

The package implements dependency-light local source planning and source-record helpers:

- `nerdbot.sources.build_source_record()` builds the source record shape without writing files.
- `nerdbot.sources.plan_text_source()` plans inline text capture under `raw/`.
- `nerdbot.sources.plan_local_file_source()` plans local-file capture and uses pointer stubs for oversized or unreadable sources.
- `nerdbot.sources.pointer_stub_text()` records inaccessible, private, remote-only, or oversized sources while preserving a stable source ID and access notes.
- `nerdbot ingest --source ... --apply` writes the planned raw capture or pointer stub and appends `indexes/source-map.md`.

These helpers do not crawl or fetch remote content by themselves. Mutating writes happen only through explicit `--apply` workflows.

## Provider Contract

Every acquisition provider should return a source record with:

- Source ID
- Original location or URL
- Raw storage path or pointer-stub path
- Capture method
- Timestamp
- Size and checksum when available
- License or access notes when known
- Intended wiki coverage

## Source Policy

- Preserve originals under `raw/` whenever access and size make that safe.
- Use pointer stubs for private URLs, credentialed sources, remote-only systems, oversized binaries, or sources whose license/access status is unclear.
- Do not crawl private or authenticated content unless the user explicitly authorizes the source and scope.
- Record license or access notes when known; use `unknown` rather than inventing rights.
- Normalize provider warnings into review items instead of silently promoting uncertain claims.

## Optional Providers

- Static fetch provider: simple pages and high-volume non-JS captures.
- Crawl4AI provider: rendered, deep, filtered, or JS-dependent pages.
- Crawlee provider: large-crawl orchestration with queue and recovery semantics, provisioned by the `crawl` extra.

When implemented, all providers must feed the same `raw/`, source-map, review-queue, and operation/activity-log contracts.

Native Markdown/text handling remains the dependency-light baseline. Crawl, Docling, PDF, VLM, and semantic adapters are planned optional lanes that should stay lazy-loaded through extras so bootstrap, inventory, lint, modes, and plan remain dependency-light.
