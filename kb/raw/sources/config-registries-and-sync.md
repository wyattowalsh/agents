---
title: Config Registries And Sync
tags:
  - kb
  - source
  - harness-sync
aliases:
  - Sync registries source
kind: source-summary
status: active
updated: 2026-05-01
source_count: 1
---

# Config Registries And Sync

## Source Record

| Field | Value |
|-------|-------|
| source_id | `config-registries-and-sync` |
| original_location | `config/sync-manifest.json`; `config/harness-surface-registry.json`; `config/mcp-registry.json`; `config/plugin-extension-registry.json`; `config/config-transaction-registry.json`; `planning/manifests/harness-fixture-support.json`; `scripts/sync_agent_stack.py`; `wagents/platforms/*.py` |
| raw_path | `kb/raw/sources/config-registries-and-sync.md` |
| capture_method | repo-local pointer summary from read-only inspection |
| captured_at | 2026-05-01 |
| size_bytes | pointer summary only |
| checksum | not captured |
| license_or_access_notes | repo-local canonical material; do not copy live secret values |
| intended_wiki_coverage | [[canonical-generated-surfaces]], [[sync-transaction-safety]], [[harness-and-platform-sync]], [[harness-fixture-gaps]] |

## Summary

`config/sync-manifest.json` is the main ledger for canonical, generated, merged, symlink, and symlinked-entry surfaces. `config/harness-surface-registry.json` classifies downstream surfaces by channel and support tier. `config/mcp-registry.json` and `config/plugin-extension-registry.json` model MCP/plugin ownership, including Chrome DevTools one-owner rules.

The practical sync implementation is split. `scripts/sync_agent_stack.py` still coordinates many live and repo sync operations, while `wagents/platforms/*.py` is the emerging adapter layer with placeholder adapters for some platforms. `config/config-transaction-registry.json` describes preview/redaction/backup/validation/rollback expectations, but the monolithic sync path is not yet a full transactional engine.

## Provenance

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| Sync surfaces are tracked with canonical/generated/merged/symlink roles. | `config/sync-manifest.json` | canonical material | Used by [[canonical-generated-surfaces]]. |
| Platform sync is split between a legacy monolith and newer adapters. | `scripts/sync_agent_stack.py`; `wagents/platforms/*.py` | canonical material | Used by [[sync-transaction-safety]]. |
| Transaction policy is richer than current implementation coverage. | `config/config-transaction-registry.json`; `scripts/sync_agent_stack.py` | canonical material | Recorded as an open gap. |
