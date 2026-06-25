---
title: Sync Rollback Capture W01
tags:
  - kb
  - raw
  - sync
  - safety
aliases:
  - Sync safety capture 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave01-partials-2026-06-25
---

# Sync Rollback Capture W01

Read-only capture of sync transaction safety posture on 2026-06-25.

## Implemented (code-backed)

| Control | Surface | Notes |
|---------|---------|-------|
| Dry/check mode | `SyncContext(apply=False)` | Preview without live writes |
| Config-drop refusal | `ConfigDropError` | Blocks merged renders that drop local keys |
| Merge preservation | platform adapters + `sync_agent_stack.py` | User-owned MCP/hook tables preserved on merge paths |
| Symlink `.bak` backup | rollback fixture tests | Backup on symlink replacement |

## Not proven end-to-end

| Gap | Why it matters |
|-----|----------------|
| Full merged-home snapshot restore | `~/.codex/config.toml`, `~/.cursor/mcp.json`, etc. lack proven one-shot rollback |
| Live home config vendoring | Out of scope per goal interview; metadata captures only |

## Executable rollback tests (pytest collect)

`tests/test_harness_rollback_fixtures.py` — 8 cases including Cursor home MCP merge preservation, Cursor CLI idempotency, Grok TOML merge preservation.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Transaction registry policy | `config/config-transaction-registry.json` | canonical repo path |
| Adapter merge behavior | `wagents/platforms/*`, `scripts/sync_agent_stack.py` | canonical repo paths |
| Rollback tests | `tests/test_harness_rollback_fixtures.py` | canonical repo path |