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
| original_location | `openspec/config.yaml`; `openspec/specs/`; `openspec/changes/archive/2026-05-01-*`; `planning/95-migration/40-openspec-archive-checklist.md`; `wagents/openspec.py`; `tests/test_openspec_cli.py` |
| raw_path | `kb/raw/sources/openspec-change-archive-source.md` |
| capture_method | repo-local pointer summary from read-only research |
| captured_at | 2026-05-01 |
| size_bytes | pointer summary only |
| checksum | not captured |
| license_or_access_notes | repo-local OpenSpec material; no external fetch required |
| intended_wiki_coverage | [[openspec-change-archive-status]], [[openspec-workflow]], [[known-risks-and-open-gaps]] |

## Summary

The agents-platform OpenSpec tree is archive-complete as of `841b9b1 docs(openspec): archive agents platform overhaul`. The completed `agents-*` child changes and parent `agents-platform-overhaul` were moved to `openspec/changes/archive/2026-05-01-*`, and their stable requirements were synced into durable `openspec/specs/*` files.

Task-complete, validation-passing, archive-ready, and archived are different states. The release archive lane prepared the archive gate and validation matrix; the later `841b9b1` archive commit is the evidence that the changes were actually archived.

## Provenance

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| OpenSpec config and specs define the active workflow and capability areas. | `openspec/config.yaml`; `openspec/specs/agent-assets/spec.md`; `openspec/specs/downstream-tooling/spec.md`; `openspec/specs/spec-workflows/spec.md` | canonical OpenSpec material | Source of workflow authority. |
| Archived change task files are preserved under `openspec/changes/archive/2026-05-01-*`. | `openspec/changes/archive/2026-05-01-*/tasks.md` | archived change files | Pointer summary; archived evidence is retained. |
| The release archive lane prepared archive readiness before archive execution. | `openspec/changes/archive/2026-05-01-agents-c09-release-archive/tasks.md`; `openspec/changes/archive/2026-05-01-agents-c09-release-archive/design.md`; `openspec/changes/archive/2026-05-01-agents-c09-release-archive/validation-matrix.md` | archived change material | Archive gate evidence. |
| Archive checklist evidence is required before claiming archive readiness for future changes. | `planning/95-migration/40-openspec-archive-checklist.md` | planning checklist | Checklist records required evidence items. |
| OpenSpec wrapper code and tests provide the repo-local CLI integration surface. | `wagents/openspec.py`; `wagents/cli.py`; `tests/test_openspec_cli.py` | implementation and tests | Rerun wrapper validation for each future archive pass. |
