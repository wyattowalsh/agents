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

The active OpenSpec change set appears task-complete but not archived. Read-only research found active change task files with checked task boxes and no archive directory in common archive locations, while the release archive checklist still records required evidence before archive readiness can be claimed.

Treat task-complete, validation-passing, and archive-ready as separate states. A future archive pass should rerun OpenSpec validation/status commands and confirm the worktree state before moving or archiving change material.

## Evidence

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| Active OpenSpec changes remain present under `openspec/changes/`. | `kb/raw/sources/openspec-change-archive-source.md` | raw source note | Pointer summary of active change inventory. |
| Task-complete does not equal archive-ready. | `kb/raw/sources/openspec-change-archive-source.md` | raw source note | Release archive and planning checklist evidence. |
| Wrapper code and tests define local OpenSpec CLI integration, but validation was not rerun in this KB batch. | `kb/raw/sources/openspec-change-archive-source.md` | raw source note | Confidence boundary. |

## Related

- [[openspec-workflow]]
- [[known-risks-and-open-gaps]]
- [[planning-corpus-and-drift-ledgers]]
