---
title: Planning Sync Inventory Capture W04
tags:
  - kb
  - raw
  - planning
  - sync
aliases:
  - Planning sync inventory capture 2026-06-25 wave04
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave04-planning-2026-06-25
---

# Planning Sync Inventory Capture W04

Read-only `planning/manifests/` inventory on 2026-06-25 (Wave 04).

## Manifest corpus layout

| Surface | Role |
|---------|------|
| `planning/README.md` | Index; prose planning corpus removed post-overhaul archive |
| `planning/manifests/repo-sync-inventory.json` | Path ownership, mode, drift policy, validation evidence |
| `planning/manifests/repo-drift-ledger.json` | Observed/assumed drift state and next actions |
| `planning/manifests/harness-fixture-support.json` | Conservative harness support and rollback posture |
| `planning/manifests/external-repo-*.json` | External repo intake/evaluation ledgers (93 rows each in final + intake) |
| `planning/manifests/*.json` (scaffold) | Compose/review/docs baselines with 0 records (placeholders) |

**Total manifest files:** 18 under `planning/manifests/` (17 JSON + 1 MD plugin install note).

## `repo-sync-inventory.json` (90 records)

| Dimension | Distribution |
|-----------|--------------|
| `mode` | canonical 31, generated 30, merged 18, symlink 7, symlinked-entries 4 |
| `location_class` | repo 52, home 34, application-support 4 |
| `drift_policy` | canonical 33, generated 31, merged 18, symlinked-entries 4, symlink 4 |
| `source_tier` | generated-output 31, canonical-source 31, merged-live-config 18, symlink-target 10 |
| `secret_handling` | not-secret-bearing 59, path-only 19, redacted 12 |

`source_ref` points at `config/sync-manifest.json`; inventory is the conservative planning mirror with per-path validation evidence and secret-handling posture.

## `harness-fixture-support.json` (19 harness rows)

| Field | Distribution |
|-------|--------------|
| `fixture_status` | fixture-executable 12, fixture-plan-only 4, docs-ledger-required 3 |
| `rollback_coverage` | present 8, planned 8, not-applicable 3 |
| `current_support_tier` | repo-present-validation-required 15, validated 2, experimental 2 |

Registry refs: `config/harness-surface-registry.json`, `config/support-tier-registry.json`.

## Operating notes

- Home and application-support paths (38 in drift ledger as `external-live`) remain path-only or externally audited; do not ingest live secrets into KB.
- Empty scaffold manifests (`compose-post-review-*.json`, `docs-composed-coverage.json`, etc.) are reserved for future compose/review waves—not evidence of missing sync rows.
- Pair this inventory with active OpenSpec changes that touch sync (`integrate-apm-package-manager`, `integrate-mcphub-control-plane`, `compose-harness-catalog-pages`).

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Record counts and distributions | `planning/manifests/*.json` | canonical repo path |
| README scope | `planning/README.md` | canonical repo path |