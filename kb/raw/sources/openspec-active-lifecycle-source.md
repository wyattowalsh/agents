---
title: OpenSpec Active Lifecycle Snapshot
tags:
  - kb
  - source
  - openspec
aliases:
  - OpenSpec active inventory
kind: source-summary
status: active
updated: 2026-06-23
source_count: 1
---

# OpenSpec Active Lifecycle Snapshot

## Source Record

| Field | Value |
|-------|-------|
| source_id | `openspec-active-lifecycle` |
| original_location | `openspec/`; `openspec/changes/`; `openspec/changes/archive/`; `wagents/openspec.py`; `wagents/cli.py`; `skills/openspec-workflow/scripts/openspec_cli.py` |
| raw_path | `kb/raw/sources/openspec-active-lifecycle-source.md` |
| capture_method | repo-local pointer summary from read-only research |
| captured_at | 2026-06-23 |
| size_bytes | pointer summary only |
| checksum | not captured |
| license_or_access_notes | repo-local canonical material |
| intended_wiki_coverage | [[openspec-change-archive-status]], [[openspec-workflow]] |

## Summary

As of 2026-06-23 inspection: approximately 32 active change proposals under `openspec/changes/<name>/` (non-archive) and 28 archived under `openspec/changes/archive/`. Recent archive batch includes `2026-06-16-*` changes. Artifact completeness varies (not all actives have design.md or validation-matrix.md).

Four active changes contained unchecked tasks at inspection time: `compose-harness-catalog-pages`, `integrate-apm-package-manager`, `integrate-mcphub-control-plane`, `public-release-prod-readiness`. Many others appeared task-complete with validation matrices asserting pass.

`wagents openspec archive` wraps `npx @fission-ai/openspec archive` with dry-run default. Portable `skills/openspec-workflow/scripts/openspec_cli.py` lacks an `archive` subcommand despite SKILL dispatch documenting it.

## Provenance

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| Artifact order and when OpenSpec required. | `openspec/config.yaml`; `openspec/schemas/agent-asset-change/schema.yaml` | canonical material | Workflow contract |
| Archive moves to dated archive dirs. | `openspec/specs/spec-workflows/spec.md` | canonical material | State distinction |
| Wrapper workflows list. | `wagents/openspec.py:34` | canonical material | Core vs expanded |
| Missing archive in portable skill CLI. | `skills/openspec-workflow/scripts/openspec_cli.py` | canonical material | Inconsistency |

## Planned wiki coverage

| Topic | Status |
|-------|--------|
| [[openspec-change-archive-status]] | refresh inventory |
| [[openspec-workflow]] | cross-link |