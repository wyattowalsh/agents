---
title: OpenSpec Change Archive Status
tags:
  - kb
  - source
  - openspec
  - archive
aliases:
  - OpenSpec archive source
  - Change archive status source
kind: source-summary
status: active
updated: 2026-05-01
source_count: 1
---

# OpenSpec Change Archive Status

## Source Record

| Field | Value |
|-------|-------|
| source_id | `openspec-change-archive-status` |
| original_location | `openspec/config.yaml`; `openspec/specs/`; `openspec/changes/*/tasks.md`; `openspec/changes/agents-c09-release-archive/`; `planning/95-migration/40-openspec-archive-checklist.md`; `wagents/openspec.py`; `tests/test_openspec_cli.py` |
| raw_path | `kb/raw/sources/openspec-change-archive-source.md` |
| capture_method | repo-local pointer summary from read-only research |
| captured_at | 2026-05-01 |
| size_bytes | pointer summary only |
| checksum | not captured |
| license_or_access_notes | repo-local OpenSpec material; no external fetch required |
| intended_wiki_coverage | [[openspec-change-archive-status]], [[openspec-workflow]], [[known-risks-and-open-gaps]] |

## Summary

The active OpenSpec tree is task-complete but not archive-complete. Read-only research found many checked tasks and no unchecked task boxes across active change task files, but no archive directory was found under common archive paths. Archive readiness still depends on evidence captured by the release archive checklist and OpenSpec validation/status commands.

Task-complete and archive-ready are different states. The release archive lane prepares the archive gate and validation matrix; it does not itself mean that changes have been archived or that the current dirty worktree is safe to treat as release-clean.

## Provenance

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| OpenSpec config and specs define the active workflow and capability areas. | `openspec/config.yaml`; `openspec/specs/agent-assets/spec.md`; `openspec/specs/downstream-tooling/spec.md`; `openspec/specs/spec-workflows/spec.md` | canonical OpenSpec material | Source of workflow authority. |
| Active change task files were found under `openspec/changes/*/tasks.md`. | `openspec/changes/*/tasks.md` | active change files | Pointer summary; no task files copied. |
| The release archive lane prepares archive readiness rather than proving archive completion. | `openspec/changes/agents-c09-release-archive/tasks.md`; `openspec/changes/agents-c09-release-archive/design.md`; `openspec/changes/agents-c09-release-archive/validation-matrix.md` | active change material | Archive gate evidence. |
| Archive checklist evidence is still required before claiming archive readiness. | `planning/95-migration/40-openspec-archive-checklist.md` | planning checklist | Checklist has required evidence items. |
| OpenSpec wrapper code and tests provide the repo-local CLI integration surface. | `wagents/openspec.py`; `wagents/cli.py`; `tests/test_openspec_cli.py` | implementation and tests | CLI validity was not rerun in this research pass. |
