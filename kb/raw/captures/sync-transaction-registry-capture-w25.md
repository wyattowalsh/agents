---
title: Sync Transaction Registry Capture W25
tags:
  - kb
  - raw
  - sync
aliases:
  - Sync transaction registry 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave25-pass4-2026-06-25
---

# Sync Transaction Registry Capture W25

Pointer to `config/config-transaction-registry.json` on 2026-06-25 (complements w03 capture).

## Role

Defines merge/drop guards and transaction semantics for `sync_agent_stack.py` home/repo projections. Linked from [[sync-transaction-safety]] and wave 03 `config-transaction-registry-capture-w03.md`.

## Safety themes

- Preserve unrelated user-owned live config while enforcing repo-managed defaults.
- Rollback coverage validated by `tests/test_harness_rollback_fixtures.py` (8 cases per w01 capture).

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Registry path | `config/config-transaction-registry.json` | canonical repo |
| W03 capture | `kb/raw/captures/config-transaction-registry-capture-w03.md` | raw capture |