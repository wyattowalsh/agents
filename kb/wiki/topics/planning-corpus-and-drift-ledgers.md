---
title: Planning Manifests And Drift Ledgers
tags:
  - kb
  - planning
  - sync
  - drift
aliases:
  - Planning manifests
  - Planning corpus
  - Drift ledgers
kind: concept
status: active
updated: 2026-05-01
source_count: 1
---

# Planning Manifests And Drift Ledgers

## Scope

This page maps the repo-local planning manifests that support sync, drift, and harness fixture claims. It is not a replacement for active OpenSpec change tasks, durable specs, or executable validation.

## Summary

The completed prose planning corpus was removed from the active tree after the agents platform overhaul was archived. The remaining active planning surface is `planning/README.md` plus machine-readable ledgers under `planning/manifests/`.

The manifest layer adds a second, more conservative view of harness sync than the public README or generated docs. It treats sync as auditable only when each managed path has ownership mode, location class, drift policy, validation evidence, and secret-handling posture recorded.

The drift ledger distinguishes repo paths from live user/application-support paths. Repo paths can be clean, dirty, untracked, or not checked. Home and application-support paths are treated as `external-live` unless a harness-specific audit safely verifies them. Generated or merged surfaces with possible credentials remain high-risk until redaction and rollback fixtures exist.

Harness fixture support is intentionally not a validated-support claim. It records fixture classes, validation commands, rollback status, and promotion blockers for each harness. Operators should cite the exact fixture/support row before raising a support tier or claiming end-to-end projection coverage.

## Operating Use

Use this page before changing sync support tiers, harness projection ownership, rollback claims, or docs that advertise harness readiness. Pair it with [[sync-transaction-safety]], [[harness-fixture-gaps]], and [[canonical-generated-surfaces]].

## Evidence

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| Sync and drift manifests record path ownership, mode, drift policy, validation evidence, and secret-handling posture. | `kb/raw/sources/planning-corpus-drift-source.md` | raw source note | Derived from active planning manifests. |
| Live user and application-support paths are path-only or external-live unless specifically audited. | `kb/raw/sources/planning-corpus-drift-source.md` | raw source note | Avoids ingesting secret-bearing live config. |
| Harness support tiers should not be raised until fixture and rollback evidence exists. | `kb/raw/sources/planning-corpus-drift-source.md` | raw source note | Keeps support claims conservative. |

## Related

- [[sync-transaction-safety]]
- [[harness-fixture-gaps]]
- [[harness-and-platform-sync]]
- [[known-risks-and-open-gaps]]
- [[repo-map]]
