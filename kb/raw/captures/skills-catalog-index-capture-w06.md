---
title: Skills Catalog Index Capture W06
tags:
  - kb
  - raw
  - docs
  - catalog
aliases:
  - Catalog index bundle 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave06-docs-authoring-2026-06-25
---

# Skills Catalog Index Capture W06

Committed machine bundle at `docs/public/generated-registries/skills-catalog-index.json`.

## Captured Facts

| Metric | Value | Method |
|--------|-------|--------|
| `allSkillIndex` entries | 363 | JSON parse |
| Inferred custom rows | 56 | `sourceKind` / `source_kind` == custom |
| Inferred curated-external rows | 307 | curated-external kind |
| Runtime SSOT | this JSON file | `wagents docs generate` default output |

## Quoted policy

> Prefer authoring MDX + index; dual-read legacy `config/external-skills.md` only when index missing.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Index entry count | `skills-catalog-index.json` | repo file read |
| Custom/external split | JSON field scan | tool capture |
| Generator ownership | `kb/raw/sources/skills-catalog-authoring-lifecycle-source.md` | prior KB source |