---
title: OpenSpec Active Changes Capture W04
tags:
  - kb
  - raw
  - openspec
aliases:
  - OpenSpec active changes capture 2026-06-25 wave04
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave04-planning-2026-06-25
---

# OpenSpec Active Changes Capture W04

Read-only OpenSpec active-change inventory on 2026-06-25 (Wave 04).

## Validation

```
uv run wagents openspec validate
→ 33/33 items passed (8 changes, 25 specs)
```

## Directory counts

| Bucket | Count | Path |
|--------|-------|------|
| Active changes | 8 | `openspec/changes/<name>/` (non-archive) |
| Archived changes | 53 | `openspec/changes/archive/` |

## Active change task posture

| Change ID | Open | Done | Archive-ready |
|-----------|------|------|---------------|
| `add-new-project-skill` | 0 | 14 | yes |
| `consolidate-review-skill` | 0 | 15 | yes |
| `enhance-skill-creator-lifecycle` | 0 | 12 | yes |
| `upgrade-design-skill` | 0 | 20 | yes |
| `compose-harness-catalog-pages` | 5 | 2 | no |
| `integrate-apm-package-manager` | 8 | 27 | no |
| `integrate-mcphub-control-plane` | 5 | 11 | no |
| `public-release-prod-readiness` | 10 | 0 | no |

Task counts include both `- [ ]` / `- [x]` and numbered `N. [ ]` / `N. [x]` checklist styles.

## Wave themes (in-flight)

- **Catalog compose:** `compose-harness-catalog-pages` — frontmatter standardization and orchestrator compose waves (supersedes docs-copy-reduction trimming).
- **APM integration:** `integrate-apm-package-manager` — remote package manager path alongside repo SSOT; doctor/catalog/sync-manifest extensions.
- **MCPHub control plane:** `integrate-mcphub-control-plane` — local MCP process ownership, groups, endpoint projection.
- **Release readiness:** `public-release-prod-readiness` — full gate matrix, fail-closed validation, public-path hygiene (all tasks open).

## Archive-ready batch (4 changes)

Four active changes have zero open tasks and non-zero completed tasks. Archive readiness still requires maintainer validation pass and explicit archive command; task-complete ≠ archived.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Validate JSON summary | `uv run wagents openspec validate` | tool capture |
| Task counts | `openspec/changes/*/tasks.md` | repo read |
| Archive dir count | `openspec/changes/archive/` | filesystem |