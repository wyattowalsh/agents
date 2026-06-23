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
updated: 2026-06-23
source_count: 3
---

# Sync Transaction Safety

## Scope

This page records the safety model and current implementation gap for live/global config writes.

## Summary

Harness sync can touch sensitive user-owned global config and repo-managed generated surfaces. The registry-level safety model in `config/config-transaction-registry.json` expects preview, redaction, backup, validation, and rollback for live writes.

**Implemented today:** `SyncContext(apply=False)` dry/check mode; `ConfigDropError` refusal when merged renders would drop local keys; merge helpers preserving user-owned MCP/hook/config entries; limited `.bak` backup on symlink replacement.

**Not proven:** Full pre-apply snapshot + restore for merged home globals (`~/.codex/config.toml`, `~/.cursor/mcp.json`, etc.). Rollback fixtures in `planning/manifests/harness-fixture-support.json` remain mostly `planned`.

Future sync changes should prefer OpenSpec, `--check` previews, redacted output, explicit backups, and targeted validation before `--apply`. Do not capture secret values into this KB.

## Evidence

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| Transaction policy describes preview/redaction/backup/validation/rollback. | `kb/raw/sources/config-registries-and-sync.md` | raw source note | Registry source. |
| Config-drop guards and merge preservation implemented. | `kb/raw/sources/wagents-platform-adapters-source.md` | raw source note | Code-backed safety. |
| Rollback contract not fully implemented per path. | `kb/raw/sources/wagents-platform-adapters-source.md` | raw source note | Conservative posture. |
| Planning ledgers classify path modes and fixture blockers. | `kb/raw/sources/planning-corpus-drift-source.md` | raw source note | Snapshot evidence. |

## Related

- [[wagents-platform-adapters]]
- [[harness-and-platform-sync]]
- [[canonical-generated-surfaces]]
- [[planning-corpus-and-drift-ledgers]]
- [[known-risks-and-open-gaps]]
