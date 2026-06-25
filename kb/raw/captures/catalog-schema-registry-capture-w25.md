---
title: Catalog Schema Registry Capture W25
tags:
  - kb
  - raw
  - catalog
aliases:
  - Catalog schema registry 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave25-pass4-2026-06-25
---

# Catalog Schema Registry Capture W25

Bucket A catalog schema pointers on 2026-06-25.

## Schema files (openspec/schemas/)

- `skills-catalog-authoring.schema.json` — authoring MDX frontmatter contract
- `skills-catalog-index.schema.json` — generated index bundle shape

## SSOT flow

`docs/src/authoring/skills/*.mdx` → `uv run wagents docs generate` → `docs/public/generated-registries/skills-catalog-index.json`

## Legacy fallback

`config/external-skills.md` — deprecated; dual-read only when index missing or `WAGENTS_CATALOG_LEGACY_EXTERNAL_MD=1`.

## Counts (wave 06 baseline)

363 authoring MDX files; 363 index rows (committed bundle).

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Bucket A policy | `AGENTS.md` §2.7 | canonical repo |
| W06 captures | `kb/raw/captures/catalog-authoring-mdx-capture-w06.md` | raw capture |