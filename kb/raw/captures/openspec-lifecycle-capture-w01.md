---
title: OpenSpec Lifecycle Capture W01
tags:
  - kb
  - raw
  - openspec
aliases:
  - OpenSpec validate capture 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave01-partials-2026-06-25
---

# OpenSpec Lifecycle Capture W01

Read-only OpenSpec lifecycle snapshot on 2026-06-25.

## Validation

```
uv run wagents openspec validate
→ 33/33 items passed (8 changes, 25 specs)
```

## Directory counts

| Bucket | Count | Path |
|--------|-------|------|
| Active changes | 9 | `openspec/changes/<name>/` (non-archive) |
| Archived changes | 53 | `openspec/changes/archive/` |

## Active change IDs (validation set)

`add-new-project-skill`, `compose-harness-catalog-pages`, `consolidate-review-skill`, `enhance-skill-creator-lifecycle`, `integrate-apm-package-manager`, `integrate-mcphub-control-plane`, `public-release-prod-readiness`, `upgrade-design-skill` (plus 25 specs).

## State distinctions

Task-complete, validation-passing, archive-ready, and archived remain separate states. Bulk 2026-06-24 archives reduced active set; remaining actives include integration and release-readiness waves with open tasks.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Validate JSON summary | `wagents openspec validate` | tool capture |
| Archive dirs | filesystem under `openspec/changes/archive/` | repo read |