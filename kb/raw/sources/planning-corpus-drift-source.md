---
title: Planning Corpus And Drift Ledgers
tags:
  - kb
  - source
  - planning
  - sync
aliases:
  - Planning corpus source
  - Drift ledgers source
kind: source-summary
status: active
updated: 2026-05-01
source_count: 1
---

# Planning Corpus And Drift Ledgers

## Source Record

| Field | Value |
|-------|-------|
| source_id | `planning-corpus-and-drift-ledgers` |
| original_location | `planning/00-overview/12-repo-sync-and-drift-ledger.md`; `planning/manifests/repo-sync-inventory.json`; `planning/manifests/repo-drift-ledger.json`; `planning/manifests/harness-fixture-support.json`; `agents-overhaul-planning/README.md` |
| raw_path | `kb/raw/sources/planning-corpus-drift-source.md` |
| capture_method | repo-local pointer summary from read-only inspection |
| captured_at | 2026-05-01 |
| size_bytes | pointer summary only |
| checksum | not captured |
| license_or_access_notes | repo-local planning material; home and application-support paths remain path-only evidence |
| intended_wiki_coverage | [[planning-corpus-and-drift-ledgers]], [[harness-fixture-gaps]], [[sync-transaction-safety]], [[known-risks-and-open-gaps]] |

## Summary

The planning corpus records how sync and harness support should become auditable before any apply step mutates user-level configuration. The repo-sync inventory classifies managed paths by ownership, mode, location class, source tier, drift policy, validation evidence, and secret-handling posture. The drift ledger records observed or assumed drift state and next actions for managed paths, including generated, merged, symlinked, and user-owned live config surfaces.

The harness fixture support manifest keeps support claims conservative. No harness is promoted to `validated` by the foundation planning pass; many surfaces remain `fixture-plan-only`, `docs-ledger-required`, `planned-research-backed`, or `experimental` until executable fixtures, rollback coverage, and first-party documentation evidence exist.

`agents-overhaul-planning/README.md` describes the broader skills-first, MCP-second, plugin/adapters-as-projection-layers posture. It also treats OpenSpec as the governance mechanism for major behavior changes and identifies docs, instructions, manifests, CI gates, skill audit, MCP audit, and OpenSpec reconciliation as first-class implementation artifacts.

## Provenance

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| Sync inventory and drift ledgers make harness synchronization auditable before apply steps mutate user-level config. | `planning/00-overview/12-repo-sync-and-drift-ledger.md` | canonical planning material | Supports sync safety and drift pages. |
| Managed paths are classified by mode, location class, source tier, drift policy, validation evidence, and secret handling. | `planning/manifests/repo-sync-inventory.json` | canonical planning material | Pointer summary only; no live secret values captured. |
| Drift state and next action are tracked per managed path. | `planning/manifests/repo-drift-ledger.json` | canonical planning material | Includes generated, merged, symlinked, and external-live surfaces. |
| Harness support is not fully validated until fixture and rollback evidence exists. | `planning/manifests/harness-fixture-support.json` | canonical planning material | Supports conservative harness claims. |
| The overhaul planning posture is skills-first, MCP-second, plugin/adapters-as-projection-layers, and OpenSpec-governed. | `agents-overhaul-planning/README.md` | canonical planning material | Context for future implementation lanes. |
