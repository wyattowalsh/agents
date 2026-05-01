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
status: active
updated: 2026-05-01
source_count: 1
---

# OpenSpec Change Archive Status

## Scope

This page captures the observed active-change/archive-readiness state. It is not a release signoff and does not replace `uv run wagents openspec validate`.

## Summary

The agents-platform OpenSpec change set was archived in `841b9b1 docs(openspec): archive agents platform overhaul`. The completed `agents-*` child changes and parent `agents-platform-overhaul` now live under `openspec/changes/archive/2026-05-01-*`, and their durable requirements were synced into `openspec/specs/*`.

Treat task-complete, validation-passing, archive-ready, and archived as separate states. A future archive pass should rerun OpenSpec validation/status commands and confirm the worktree state before moving or archiving change material.

## Evidence

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| Agents-platform changes are archived under `openspec/changes/archive/2026-05-01-*`. | `kb/raw/sources/openspec-change-archive-source.md` | raw source note | Current archive inventory after `841b9b1`. |
| Task-complete does not equal archive-ready or archived. | `kb/raw/sources/openspec-change-archive-source.md` | raw source note | Preserved workflow distinction for future changes. |
| Wrapper code and tests define local OpenSpec CLI integration. | `kb/raw/sources/openspec-change-archive-source.md` | raw source note | Validation should still be rerun for each future archive pass. |

## Related

- [[openspec-workflow]]
- [[known-risks-and-open-gaps]]
- [[planning-corpus-and-drift-ledgers]]
