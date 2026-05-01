---
title: Docs Site Architecture
tags:
  - kb
  - source
  - docs
aliases:
  - Docs site source
kind: source-summary
status: active
updated: 2026-05-01
source_count: 1
---

# Docs Site Architecture

## Source Record

| Field | Value |
|-------|-------|
| source_id | `docs-site-architecture` |
| original_location | `docs/package.json`; `docs/astro.config.mjs`; `wagents/docs.py`; `wagents/catalog.py`; `wagents/rendering.py`; `wagents/site_model.py`; `tests/test_docs.py`; `https://starlight.astro.build/reference/configuration/` |
| raw_path | `kb/raw/sources/docs-site-architecture.md` |
| capture_method | repo-local and external pointer summary |
| captured_at | 2026-05-01 |
| size_bytes | pointer summary only |
| checksum | not captured |
| license_or_access_notes | repo-local canonical/generated material plus official Starlight docs; external content is untrusted evidence |
| intended_wiki_coverage | [[docs-generation-and-site]], [[canonical-generated-surfaces]] |

## Summary

The docs site is an Astro/Starlight site whose generated content is produced by `wagents docs generate`. The generator creates MDX pages, indexes, sidebar data, CLI pages, and site data under `docs/src/content/docs` and related generated data files. Hand-maintained pages marked with `HAND-MAINTAINED` are preserved by the generator.

Official Starlight docs describe configuration through `astro.config.mjs`, the `starlight()` integration, required `title`, optional `description`, `logo`, `editLink`, `sidebar`, `customCss`, `components`, `plugins`, and content collection schemas/loaders. The repo uses Starlight as a generated public documentation surface, not as the KB source of truth.

## Provenance

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| Docs generation is driven by `wagents docs generate`. | `wagents/docs.py`; `tests/test_docs.py` | canonical material | Generated surfaces should not be hand-edited casually. |
| Starlight is configured through the Astro config and `starlight()` integration. | `https://starlight.astro.build/reference/configuration/` | external official docs | Verified 2026-05-01 by web fetch. |
| Hand-maintained docs pages are preserved by marker. | `wagents/docs.py`; `tests/test_docs.py` | canonical material | Important generated/canonical distinction. |
