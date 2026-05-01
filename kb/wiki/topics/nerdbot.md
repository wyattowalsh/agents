---
title: Nerdbot In This Repository
tags:
  - kb
  - nerdbot
  - obsidian
aliases:
  - Nerdbot KB maintenance
kind: concept
status: active
updated: 2026-05-01
source_count: 4
---

# Nerdbot In This Repository

## How Nerdbot Applies Here

This KB uses the Nerdbot pattern to separate evidence from synthesis:

| Layer | Local use |
|-------|-----------|
| `raw/` | Source notes, captures, extracts, and asset intake pointers. |
| `wiki/` | Short, linked operating knowledge pages for future agents. |
| `schema/` | Page and provenance contracts. |
| `config/` | Obsidian vault conventions. |
| `indexes/` | Source map, coverage map, repository map, and glossary. |
| `activity/log.md` | Append-only mutating-batch history and next gaps. |

## Maintenance Rules

- Add source notes under `raw/sources/` before broad synthesis.
- Keep claims in `wiki/` backed by `raw` source notes or declared canonical material.
- Update `indexes/source-map.md`, `indexes/coverage.md`, and `activity/log.md` in the same batch as new wiki pages.
- Use pointer stubs instead of copying huge, binary, private, symlinked, or secret-looking sources.
- Keep volatile Obsidian workspace state out of the KB.
- Run `uv run --project skills/nerdbot nerdbot inventory --root ./kb` and `uv run --project skills/nerdbot nerdbot lint --root ./kb --include-unlayered` before claiming KB health.

## Markdown-Only Session Constraint

This initial batch created Markdown files only. If future operators want CSS snippets or other non-Markdown vault assets, add them in a non-plan execution context after reviewing the shared `.obsidian/` policy.

## Runtime Checks

For this repository's KB, inventory and lint are the completion gates. Inventory confirms the layer/vault shape; lint checks provenance, index freshness, Obsidian links, embeds, aliases, required starter files, and activity-log coverage. External Obsidian and Markdown docs are captured only to clarify syntax and vault conventions; Nerdbot's local contract remains authoritative.

## Related Pages

- [[repository-overview]]
- [[developer-commands]]
- [[validation-and-test-coverage]]
- [[external-primary-source-map]]
- [[known-risks-and-open-gaps]]
- [[coverage]]

## Evidence

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| Nerdbot separates `raw`, `wiki`, `schema`, `config`, `indexes`, and `activity/log.md`. | `kb/raw/sources/nerdbot-skill-contract.md` | raw source note | Derived from Nerdbot skill and README. |
| Query and audit flows are read-only by default. | `kb/raw/sources/nerdbot-skill-contract.md` | raw source note | Derived from Nerdbot README. |
| Local-file ingest uses pointer stubs for outside-root, symlinked, oversized, unreadable, or secret-looking files unless explicitly approved. | `kb/raw/sources/nerdbot-skill-contract.md` | raw source note | Derived from Nerdbot README. |
| Shared `.obsidian/` surfaces should exclude volatile workspace state by default. | `kb/raw/sources/nerdbot-skill-contract.md` | raw source note | Derived from loaded Obsidian vault guidance. |
| Nerdbot inventory and lint are the targeted KB verification commands for this work. | `kb/raw/sources/nerdbot-runtime-contracts.md`; `kb/raw/extracts/developer-commands-extract.md` | raw source notes | Runtime contract and command extract. |
| Obsidian and Markdown upstream docs are contextual syntax references only. | `kb/raw/sources/external-obsidian-markdown-docs.md` | external source note | Local Nerdbot contract remains authoritative. |
