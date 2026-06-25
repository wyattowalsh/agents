---
title: Sync Manifest Snapshot Capture W17
tags:
  - kb
  - raw
  - sync
aliases:
  - Sync manifest 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave17-pass2-2026-06-25
---

# Sync Manifest Snapshot Capture W17

Read-only pointer summary from `config/sync-manifest.json` on 2026-06-25.

## Snapshot

| Field | Value |
|-------|-------|
| `version` | 1 |
| `managed[]` length | **90** canonical/generated/merged surface records |

## Role

Records canonical vs generated vs merged vs symlinked surfaces for harness stack sync. Consumed by `scripts/sync_agent_stack.py` and `wagents/platforms/*` adapters. Pair with `config/config-transaction-registry.json` for rollback/merge modes.

## Related registries

| File | Purpose |
|------|---------|
| `config/sync-manifest.json` | Surface ownership and sync mode |
| `config/config-transaction-registry.json` | Transaction safety contract |
| `config/harness-surface-registry.json` | Per-harness projection claims |
| `planning/manifests/sync-inventory.json` | Planning parity ledger (90 rows, wave 04) |

## Interpretation

Do not edit generated/home targets without tracing back to manifest canonical source. Full entry enumeration lives in canonical JSON — this capture is a navigation anchor, not a vendored manifest.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Manifest path | `config/sync-manifest.json` | canonical repo |
| Transaction pairing | `kb/raw/captures/config-transaction-registry-capture-w03.md` | raw capture |