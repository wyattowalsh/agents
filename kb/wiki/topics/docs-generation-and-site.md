---
title: Docs Generation And Site
tags:
  - kb
  - docs
  - starlight
aliases:
  - Docs site
kind: concept
status: active
updated: 2026-06-25
source_count: 10
---

# Docs Generation And Site

## Scope

This page covers the generated public docs surface. It does not replace `/docs-steward` or claim the current docs build passes.

## Summary

The public docs site is an Astro/Starlight site under `docs/`. `wagents docs generate` creates generated MDX content, indexes, sidebar data, CLI pages, and site data. `wagents docs build` runs generation and then the docs build. Generated pages should not be hand-edited unless explicitly promoted or marked as hand-maintained.

Official Starlight docs confirm that Starlight is configured through `astro.config.mjs` using the `starlight()` integration. Options such as title, description, logo, edit links, sidebar, custom CSS, components, plugins, content loaders, and schemas are relevant to this repo's docs site architecture.

## Artifact Freshness

`config/docs-artifact-registry.json` tracks selected generated docs artifacts and validation commands, but the docs generator writes more surfaces than the registry currently enumerates. README freshness has a non-mutating check via `uv run wagents readme --check`; docs generation does not yet have an equivalent `wagents docs generate --check` command.

**2026-06-25 freshness:** Compose coverage is **397/397 (100%)** including 22 hook pages and 363 skill pages (`wagents docs compose --check-composed --min-pct 100`). CI enforces `wagents docs generate --no-installed --check` and compose 100% on PR/push (`.github/workflows/ci.yml`).

**Remaining hand-maintained drift:** `docs/src/content/docs/mcp/index.mdx` badge still shows "15 configured servers" while `config/mcp-registry.json` lists **33** servers — a docs copy fix outside KB scope once tracked in [[known-risks-and-open-gaps]].

`config/docs-artifact-registry.json` still enumerates a subset of generated surfaces; the generator emits additional indexes and site data beyond that registry.

## Evidence

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| Docs generation is driven by `wagents docs generate`. | `kb/raw/sources/docs-site-architecture.md`; `kb/raw/sources/wagents-internals.md` | raw source notes | Local implementation is authoritative. |
| Starlight config lives in Astro config and uses `starlight()`. | `kb/raw/sources/docs-site-architecture.md`; `kb/raw/sources/external-tooling-docs.md` | external source notes | Official Starlight docs verified. |
| Generated docs are source-derived surfaces. | `kb/raw/sources/docs-site-architecture.md`; `kb/raw/sources/config-registries-and-sync.md` | raw source notes | Update via generator, not generic note edits. |
| Compose 100% and CI generate --check gates. | `kb/raw/captures/docs-freshness-capture-w01.md` | raw capture | 2026-06-25 tool capture. |
| MCP badge vs registry cardinality drift. | `kb/raw/captures/docs-freshness-capture-w01.md` | raw capture | 15 vs 33 servers. |
| Docs artifact registry partial enumeration. | `kb/raw/sources/docs-artifact-freshness.md` | raw source note | Registry subset vs generator output. |
| Catalog index 363 rows (56 custom / 307 external). | `kb/raw/captures/skills-catalog-index-capture-w06.md` | raw capture | 2026-06-25 JSON scan. |
| Authoring MDX flat corpus 363 files. | `kb/raw/captures/catalog-authoring-mdx-capture-w06.md` | raw capture | Bucket A SSOT count. |
| Generate --check CI + catalog index check policy. | `kb/raw/captures/docs-generate-check-capture-w06.md` | raw capture | Freshness gates. |

## Related

- [[wagents-cli-and-automation]]
- [[canonical-generated-surfaces]]
- [[known-risks-and-open-gaps]]
- [[validation-and-test-coverage]]
