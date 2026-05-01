# Implementation Charter

## Purpose

Use this charter to keep the Nerdbot overhaul aligned with the existing skill contract while the package grows from compatibility scripts into a full local-first knowledge system.

## Non-Negotiable Promises

- Inventory-first: inspect the KB or repo before any mutating action.
- Additive-first: prefer new layers, indexes, stubs, queues, and annotations over rewrites.
- Raw append-only: preserve originals in `raw/`; add normalized extracts beside them.
- Provenance mandatory: every substantive `wiki/` claim must trace to `raw` or declared `canonical material`.
- Query and audit read-only: no save-back unless the user explicitly asks for `enrich`, `ingest`, `derive`, or review-queue work.
- Activity append-only: append `activity/log.md` entries instead of rewriting history.
- Migration approval: require explicit approval for moves, renames, deletes, cutovers, destructive rewrites, or canonical-material replacement.

## Build Order

1. Preserve existing `scripts/kb_bootstrap.py`, `scripts/kb_inventory.py`, and `scripts/kb_lint.py` behavior.
2. Add an installable package and CLI that delegates to the compatibility layer.
3. Move reusable logic behind typed internal modules without breaking script imports.
4. Add optional adapters for crawling, document conversion, semantic search, graph analysis, watch mode, and replay.
5. Keep heavyweight integrations optional and locally executable.

## Out Of Scope

- Hosted-only services as required baseline dependencies.
- Cloud vector databases as a default storage layer.
- Unapproved rewrites of user-authored notes or canonical material.
- Vendoring external llm-wiki repositories or shelling out to them as implementation.
