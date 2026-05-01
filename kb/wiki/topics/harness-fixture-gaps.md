---
title: Harness Fixture Gaps
tags:
  - kb
  - harness-sync
  - gaps
aliases:
  - Fixture gaps
kind: concept
status: active
updated: 2026-05-01
source_count: 2
---

# Harness Fixture Gaps

## Scope

This page records what should not be over-claimed about harness support.

## Summary

The repo supports many harnesses, but support tiers and fixture coverage differ. `planning/manifests/harness-fixture-support.json` marks many surfaces as fixture-plan-only or docs-ledger-required, so the KB should not imply every harness projection is fully validated end to end.

Future harness work should name the exact surface being changed, the registry row or sync manifest row backing it, the fixture/test that verifies it, and the rollback path for any live config mutation.

## Evidence

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| Harness support has varied support tiers and fixture status. | `kb/raw/sources/config-registries-and-sync.md` | raw source note | Avoid over-claiming. |
| Some adapters are placeholders while legacy sync remains active. | `kb/raw/sources/config-registries-and-sync.md` | raw source note | Implementation gap. |
| Fixture support rows include fixture classes, validation commands, rollback status, and promotion blockers. | `kb/raw/sources/planning-corpus-drift-source.md` | raw source note | Planning manifest keeps support claims conservative. |

## Related

- [[harness-and-platform-sync]]
- [[sync-transaction-safety]]
- [[planning-corpus-and-drift-ledgers]]
- [[known-risks-and-open-gaps]]
