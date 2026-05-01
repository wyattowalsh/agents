---
title: Nerdbot Runtime Contracts
tags:
  - kb
  - source
  - nerdbot
aliases:
  - Nerdbot runtime source
kind: source-summary
status: active
updated: 2026-05-01
source_count: 1
---

# Nerdbot Runtime Contracts

## Source Record

| Field | Value |
|-------|-------|
| source_id | `nerdbot-runtime-contracts` |
| original_location | `skills/nerdbot/src/nerdbot/contracts.py`; `skills/nerdbot/src/nerdbot/cli.py`; `skills/nerdbot/src/nerdbot/workflows.py`; `skills/nerdbot/src/nerdbot/safety.py`; `skills/nerdbot/src/nerdbot/sources.py`; `skills/nerdbot/src/nerdbot/retrieval.py`; `skills/nerdbot/src/nerdbot/graph.py`; `tests/test_nerdbot*.py` |
| raw_path | `kb/raw/sources/nerdbot-runtime-contracts.md` |
| capture_method | repo-local pointer summary from read-only inspection |
| captured_at | 2026-05-01 |
| size_bytes | pointer summary only |
| checksum | not captured |
| license_or_access_notes | repo-local canonical material |
| intended_wiki_coverage | [[nerdbot]], [[mcp-configuration-and-safety]], [[known-risks-and-open-gaps]] |

## Summary

Nerdbot workflow modes are `create`, `ingest`, `enrich`, `audit`, `query`, `derive`, `improve`, and `migrate`. `audit` and `query` are read-only modes; utility commands include `bootstrap`, `inventory`, `lint`, `plan`, `modes`, `replay`, and `watch-classify`. Write-capable workflow commands default to dry-run unless `--apply`; `migrate --apply` requires `--approval-token APPROVE-MIGRATION` and writes an additive migration plan rather than moving/deleting content.

Source safety rejects unsafe paths, symlinked/reparse roots, hardlink mutation, raw overwrite by default, and secret-looking or oversized local sources. Local-file ingest uses pointer stubs when copying is unsafe or outside the KB root. Query searches `wiki/` and `indexes/` first, builds transient FTS when no persisted FTS index exists, and warns when retrieved snippets look instruction-like.

## Provenance

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| Nerdbot mode vocabulary is fixed by runtime contracts. | `skills/nerdbot/src/nerdbot/contracts.py`; `tests/test_nerdbot*.py` | canonical material | Extending modes requires tests. |
| Local-file ingest uses pointer stubs for unsafe sources. | `skills/nerdbot/src/nerdbot/safety.py`; `skills/nerdbot/src/nerdbot/sources.py` | canonical material | Supports secret-safe KB behavior. |
| Query is read-only and searches maintained synthesis before raw evidence. | `skills/nerdbot/src/nerdbot/retrieval.py`; `tests/test_nerdbot_workflows.py` | canonical material | Matches skill contract. |
