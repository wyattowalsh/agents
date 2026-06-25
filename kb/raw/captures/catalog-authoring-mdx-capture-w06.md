---
title: Catalog Authoring MDX Capture W06
tags:
  - kb
  - raw
  - docs
  - catalog
aliases:
  - Authoring MDX inventory 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave06-docs-authoring-2026-06-25
---

# Catalog Authoring MDX Capture W06

Flat Bucket A SSOT under `docs/src/authoring/skills/*.mdx`.

## Captured Facts

| Metric | Value | Method |
|--------|-------|--------|
| Authoring MDX files | 363 | `ls docs/src/authoring/skills \| wc -l` |
| Naming convention | kebab-case id matches skill/catalog id | directory listing sample |
| Source kinds | `custom` and `curated-external` per frontmatter | index + AGENTS §2.7 |

## Scope

Human-authored catalog rows live here; `wagents docs generate` emits machine bundle and derived catalog pages. Do not hand-edit `docs/src/content/docs/skills/catalog/**` or `skills-catalog-index.json` except via generator.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Bucket A authoring path | `AGENTS.md` §2.7 | canonical repo policy |
| MDX count | filesystem listing | tool capture |