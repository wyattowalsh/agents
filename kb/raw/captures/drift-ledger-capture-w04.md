---
title: Drift Ledger Capture W04
tags:
  - kb
  - raw
  - planning
  - drift
aliases:
  - Drift ledger capture 2026-06-25 wave04
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave04-planning-2026-06-25
---

# Drift Ledger Capture W04

Read-only `planning/manifests/repo-drift-ledger.json` snapshot on 2026-06-25 (Wave 04).

## Ledger shape

| Field | Value |
|-------|-------|
| Version | 1 |
| Records | 90 (parity with `repo-sync-inventory.json`) |
| `source_refs` | `config/sync-manifest.json`, `planning/manifests/repo-sync-inventory.json`, git-status observation note |

## `current_state` distribution

| State | Count | Interpretation |
|-------|-------|----------------|
| `external-live` | 38 | Home/app-support paths; not repo-audited |
| `tracked-dirty` | 24 | Repo paths with uncommitted drift |
| `generated-live` | 14 | Generated surfaces present but may need regen |
| `not-checked` | 11 | Awaiting explicit audit |
| `tracked-clean` | 2 | In sync with expected mode |
| `untracked` | 1 | Path exists outside expected tracking |

All 90 rows carry `location_class: repo` in the ledger schema; home/app-support semantics flow through path templates and `external-live` state.

## `drift_risk` distribution

| Risk | Count |
|------|-------|
| medium | 66 |
| high | 22 |
| low | 2 |

High-risk rows cluster on merged live config, symlink targets, and generated surfaces with credential-adjacent paths.

## `next_action` top drivers

| Next action | Count |
|-------------|-------|
| `validate-before-sync` | 32 |
| `regenerate-from-canonical-source` | 26 |
| `merge-with-redaction` | 18 |
| `verify-symlink-target` | 7 |
| `document-experimental-state` | 4 |
| `verify-sync-manifest` | 2 |
| `preserve-user-changes` | 1 |

## Owner-change concentration

Top `owner_change` buckets: `agents-c04-opencode-gemini-harness` (16), `agents-c04-copilot-harness` (12), `agents-c04-cursor-harness` (10), `opencode-plugin-expansion` (10).

Use owner_change to route drift remediation to the matching harness OpenSpec archive or active wave before raising global sync support tiers.

## KB operating rule

Drift ledger rows are conservative planning evidence. They do not override `uv run wagents validate` or executable rollback fixtures documented in [[harness-fixture-gaps]].

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| State/risk/action distributions | `planning/manifests/repo-drift-ledger.json` | canonical repo path |
| Parity with sync inventory | row count compare vs `repo-sync-inventory.json` | repo read |