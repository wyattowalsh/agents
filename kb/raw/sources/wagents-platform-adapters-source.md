---
title: Wagents Platform Adapters
tags:
  - kb
  - source
  - sync
  - platforms
aliases:
  - Platform adapters source
kind: source-summary
status: active
updated: 2026-06-23
source_count: 1
---

# Wagents Platform Adapters

## Source Record

| Field | Value |
|-------|-------|
| source_id | `wagents-platform-adapters` |
| original_location | `wagents/platforms/*.py`; `wagents/platforms/__init__.py`; `scripts/sync_agent_stack.py`; `config/sync-manifest.json`; `config/config-transaction-registry.json`; `planning/manifests/harness-fixture-support.json` |
| raw_path | `kb/raw/sources/wagents-platform-adapters-source.md` |
| capture_method | repo-local pointer summary from read-only research |
| captured_at | 2026-06-23 |
| size_bytes | pointer summary only |
| checksum | not captured |
| license_or_access_notes | repo-local canonical material |
| intended_wiki_coverage | [[wagents-platform-adapters]], [[sync-transaction-safety]], [[harness-fixture-gaps]], [[harness-and-platform-sync]] |

## Summary

Harness sync projects repo-managed assets into per-platform surfaces via a dual implementation: the legacy monolith `scripts/sync_agent_stack.py` and emerging adapters under `wagents/platforms/` (cursor, codex, grok, opencode, copilot, gemini, vscode, base). `SyncContext(apply=False)` enables dry/check mode; writes occur only when `apply=True`.

Implemented safety includes config-drop refusal (`ConfigDropError`), merge helpers that preserve user-owned MCP/hook/config entries, and symlink backup via `.bak` for some paths. Declared transaction rules in `config/config-transaction-registry.json` require preview, backup, validate, and rollback for merged globals, but full rollback restore is not proven for every merged home path.

Fixture support manifest records per-harness `fixture_status` and `rollback_coverage`; most rollback fixtures remain `planned` rather than executable.

## Provenance

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| Platforms adapters registered and called from sync. | `wagents/platforms/__init__.py`; `scripts/sync_agent_stack.py` | canonical material | Dual-path implementation |
| Config-drop protection on merged writes. | `wagents/platforms/base.py` | canonical material | Tested in `test_sync_agent_stack.py` |
| Transaction registry declares rollback contract. | `config/config-transaction-registry.json` | canonical material | Implementation gap noted |
| Fixture manifest tracks promotion blockers. | `planning/manifests/harness-fixture-support.json` | canonical material | Snapshot evidence |

## Planned wiki coverage

| Topic | Status |
|-------|--------|
| [[wagents-platform-adapters]] | primary synthesis |
| [[sync-transaction-safety]] | deep enrich |
| [[harness-fixture-gaps]] | deep enrich |