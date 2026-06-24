---
title: OpenSpec Change Archive Status
tags:
  - kb
  - openspec
  - archive
aliases:
  - OpenSpec archive status
  - Active change status
kind: concept
status: partial
updated: 2026-06-24
source_count: 2
---

# OpenSpec Change Archive Status

## Scope

This page captures the observed active-change/archive-readiness state. It is not a release signoff and does not replace `uv run wagents openspec validate`.

## Summary

Historical agents-platform changes were archived in `841b9b1` under `openspec/changes/archive/2026-05-01-*`. A June 2026 archive batch added changes such as `2026-06-16-invert-catalog-*` and related catalog/discovery work.

**2026-06-23 inventory (file inspection, validation not rerun):** ~32 active proposals under `openspec/changes/<name>/` and ~28 archived under `openspec/changes/archive/`. Four actives had unchecked tasks: `compose-harness-catalog-pages`, `integrate-apm-package-manager`, `integrate-mcphub-control-plane`, `public-release-prod-readiness`. Many others appeared task-complete with validation matrices.

**2026-06-24 archive batch:** Archived `harden-skill-catalog-quality` (shipped 5dc7ec1, f33d2c7) and `add-grok-delegate-skill` (earlier). Both had all tasks checked and passed pre-archive validations (`wagents openspec validate`, `wagents validate`). Now under `openspec/changes/archive/2026-06-24-*`. Post-archive active count ~30 changes + 25 specs (all valid).

Treat task-complete, validation-passing, archive-ready, and archived as separate states. Portable `openspec_cli.py` lacks an `archive` subcommand despite SKILL dispatch documenting it.

## Evidence

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| May 2026 agents-platform archive batch. | `kb/raw/sources/openspec-change-archive-source.md` | raw source note | Historical |
| June 2026 active/archive counts and incomplete actives. | `kb/raw/sources/openspec-active-lifecycle-source.md` | raw source note | Snapshot only |
| Task-complete does not equal archive-ready or archived. | `kb/raw/sources/openspec-change-archive-source.md` | raw source note | Workflow distinction |
| Portable skill CLI missing archive handler. | `kb/raw/sources/openspec-active-lifecycle-source.md` | raw source note | Consistency gap |
| 2026-06-24 archive of harden-skill-catalog-quality and add-grok-delegate-skill. | (CLI + file moves) | archive command output | See `openspec/changes/archive/2026-06-24-*` |

## Related

- [[openspec-workflow]]
- [[known-risks-and-open-gaps]]
- [[planning-corpus-and-drift-ledgers]]
