---
title: Planning Manifests And Drift Ledgers
tags:
  - kb
  - source
  - planning
  - sync
aliases:
  - Planning manifests source
  - Planning corpus source
  - Drift ledgers source
kind: source-summary
status: active
updated: 2026-05-01
source_count: 1
---

# Planning Manifests And Drift Ledgers

## Source Record

| Field | Value |
|-------|-------|
| source_id | `planning-corpus-and-drift-ledgers` |
| original_location | `planning/README.md`; `planning/manifests/repo-sync-inventory.json`; `planning/manifests/repo-drift-ledger.json`; `planning/manifests/harness-fixture-support.json`; `openspec/changes/archive/2026-05-01-*` |
| raw_path | `kb/raw/sources/planning-corpus-drift-source.md` |
| capture_method | repo-local pointer summary from read-only inspection |
| captured_at | 2026-05-01 |
| size_bytes | pointer summary only |
| checksum | not captured |
| license_or_access_notes | repo-local planning material; home and application-support paths remain path-only evidence |
| intended_wiki_coverage | [[planning-corpus-and-drift-ledgers]], [[harness-fixture-gaps]], [[sync-transaction-safety]], [[known-risks-and-open-gaps]] |

## Summary

The active planning surface now consists of machine-readable manifests under `planning/manifests/`. Completed prose planning docs were removed from the active tree after the agents platform overhaul was archived. Historical planning evidence remains in git history and the archived OpenSpec changes under `openspec/changes/archive/2026-05-01-*`.

The repo-sync inventory classifies managed paths by ownership, mode, location class, source tier, drift policy, validation evidence, and secret-handling posture. The drift ledger records observed or assumed drift state and next actions for managed paths, including generated, merged, symlinked, and user-owned live config surfaces.

The harness fixture support manifest keeps support claims conservative. No harness is promoted to `validated` by the foundation planning pass; many surfaces remain `fixture-plan-only`, `docs-ledger-required`, `planned-research-backed`, or `experimental` until executable fixtures, rollback coverage, and first-party documentation evidence exist.

Use durable OpenSpec specs for current requirements. Future planning work should start as a new OpenSpec change rather than restoring removed finished planning docs.

## Provenance

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| Active planning docs were reduced to a manifest index plus machine-readable ledgers after the agents platform archive. | `planning/README.md`; `openspec/changes/archive/2026-05-01-*` | current index and archived OpenSpec evidence | Completed prose planning docs are not active guidance. |
| Managed paths are classified by mode, location class, source tier, drift policy, validation evidence, and secret handling. | `planning/manifests/repo-sync-inventory.json` | canonical planning material | Pointer summary only; no live secret values captured. |
| Drift state and next action are tracked per managed path. | `planning/manifests/repo-drift-ledger.json` | canonical planning material | Includes generated, merged, symlinked, and external-live surfaces. |
| Harness support is not fully validated until fixture and rollback evidence exists. | `planning/manifests/harness-fixture-support.json` | canonical planning material | Supports conservative harness claims. |
