---
title: Sync Transaction Safety
tags:
  - kb
  - sync
  - safety
aliases:
  - Config transaction safety
kind: concept
status: partial
updated: 2026-05-01
source_count: 2
---

# Sync Transaction Safety

## Scope

This page records the safety model and current implementation gap for live/global config writes.

## Summary

Harness sync can touch sensitive user-owned global config and repo-managed generated surfaces. The registry-level safety model expects preview, redaction, backup, validation, and rollback for live writes. The current practical implementation is still split between `scripts/sync_agent_stack.py` and emerging `wagents/platforms` adapters, so full transactional rollback should not be assumed for every harness.

Future work that changes sync behavior should prefer OpenSpec, dry-run previews, redacted output, explicit backups, and targeted validation before apply. It should not read or capture secret values into this KB.

## Evidence

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| Transaction policy describes preview/redaction/backup/validation/rollback. | `kb/raw/sources/config-registries-and-sync.md` | raw source note | Registry source. |
| Current implementation is split between monolith and adapters. | `kb/raw/sources/config-registries-and-sync.md` | raw source note | Implementation gap. |
| Planning ledgers classify generated, merged, symlinked, repo, home, and application-support paths with drift and secret-handling posture. | `kb/raw/sources/planning-corpus-drift-source.md` | raw source note | Use before sync support claims. |

## Related

- [[harness-and-platform-sync]]
- [[canonical-generated-surfaces]]
- [[planning-corpus-and-drift-ledgers]]
- [[known-risks-and-open-gaps]]
