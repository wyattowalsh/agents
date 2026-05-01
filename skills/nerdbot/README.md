# Nerdbot

Nerdbot creates, audits, queries, and maintains Obsidian-native, git-friendly knowledge bases with separated evidence and synthesis layers.

The current package keeps the original helper scripts available while adding an installable CLI surface, structured contract modules, review queues, dependency-light lexical retrieval, SQLite FTS5/BM25 retrieval, Markdown/Obsidian graph extraction, generated graph artifacts, safe source capture, and watch/replay policy helpers. Full acquisition adapters and optional semantic/VLM parsing remain planned lanes unless a later implementation and tests add them.

## Core Contract

- `raw/` stores source captures, originals, extracts, and assets.
- `wiki/` stores synthesized human-readable knowledge.
- `schema/` and `config/` store contracts and operational settings.
- `indexes/` stores coverage maps, source maps, inventories, and navigation.
- `activity/log.md` records every mutating batch and is append-only.
- Query and audit flows are read-only by default.

## CLI

Use bare `nerdbot` after installing the package into your environment. From this repository checkout, use `uv run --project skills/nerdbot nerdbot` so the command runs against the local package safely.

```bash
uv run --project skills/nerdbot nerdbot --help
uv run --project skills/nerdbot nerdbot bootstrap --root ./my-kb --dry-run
uv run --project skills/nerdbot nerdbot inventory --root ./my-kb
uv run --project skills/nerdbot nerdbot lint --root ./my-kb --include-unlayered
uv run --project skills/nerdbot nerdbot plan --mode ingest --target ./incoming/source.pdf
uv run --project skills/nerdbot nerdbot modes
uv run --project skills/nerdbot nerdbot plan --mode query --target ./my-kb --view guide
```

`modes` and `plan --view guide` provide polished, terminal-friendly workflow cards for humans with risk posture, gate path, safety promises, and copy-friendly next commands. The default JSON output remains available for agents, hooks, and CI.

Running `nerdbot` with no arguments prints the mode gallery and exits successfully, which makes headless invocation safe. `plan` payloads preserve the human `suggested_next_command` and include `suggested_next_argv` for callers that need shell-safe execution.

The legacy scripts remain supported:

```bash
uv run python skills/nerdbot/scripts/kb_bootstrap.py --root ./my-kb --dry-run
uv run python skills/nerdbot/scripts/kb_inventory.py --root ./my-kb
uv run python skills/nerdbot/scripts/kb_lint.py --root ./my-kb
```

## First KB Walkthrough

Start with dry-run and read-only checks before any mutating step:

```bash
uv run --project skills/nerdbot nerdbot bootstrap --root ./my-kb --dry-run
uv run --project skills/nerdbot nerdbot bootstrap --root ./my-kb
uv run --project skills/nerdbot nerdbot inventory --root ./my-kb
uv run --project skills/nerdbot nerdbot lint --root ./my-kb --include-unlayered
uv run --project skills/nerdbot nerdbot plan --mode query --target ./my-kb --view guide
uv run --project skills/nerdbot nerdbot plan --mode ingest --target ./incoming/source.pdf --view guide
```

Safe/read-only commands include `bootstrap --dry-run`, `inventory`, `lint`, `modes`, `plan`, `audit`, `query`, `replay`, and `watch-classify`. Mutating workflow commands stay dry-run until `--apply`; migration apply also requires `--approval-token APPROVE-MIGRATION` and still writes only an additive migration plan.

## Optional Lanes

Nerdbot keeps advanced dependencies optional so the safe baseline remains fast and local. Implemented generated lanes include SQLite FTS5/BM25 and Markdown/Obsidian graph reports. Planned optional lanes include Crawl4AI, Crawlee, Docling Slim, Granite VLM through the separate `vlm` extra, OpenDataLoader PDF, MarkItDown fallback conversion, and optional local semantic embeddings.

## Durable Contracts

- `nerdbot.sources` defines source records, deterministic source IDs, checksums, raw paths, and pointer-stub text.
- `nerdbot.evidence` defines evidence-ledger claims, review-queue items, freshness classes, review statuses, and confidence caps.
- `nerdbot.operations` defines append-friendly, unique operation journal entries for replayable mutating work.
- `nerdbot.retrieval` implements dependency-light lexical search and SQLite FTS5/BM25 search across `wiki/` and `indexes/`.
- `nerdbot.graph` extracts rebuildable graph edges from Markdown links, Obsidian wikilinks, embeds, aliases, and source citations.
- `nerdbot.watch`, `nerdbot.replay`, and `nerdbot.research` provide non-mutating policy helpers for watch classification, dry-run replay, and autoresearcher save-back gates.
