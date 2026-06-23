---
title: Docs Generation And Site
tags:
  - kb
  - docs
  - starlight
aliases:
  - Docs site
kind: concept
status: partial
updated: 2026-06-23
source_count: 6
---

# Docs Generation And Site

## Scope

This page covers the generated public docs surface. It does not replace `/docs-steward` or claim the current docs build passes.

## Summary

The public docs site is an Astro/Starlight site under `docs/`. `wagents docs generate` creates generated MDX content, indexes, sidebar data, CLI pages, and site data. `wagents docs build` runs generation and then the docs build. Generated pages should not be hand-edited unless explicitly promoted or marked as hand-maintained.

Official Starlight docs confirm that Starlight is configured through `astro.config.mjs` using the `starlight()` integration. Options such as title, description, logo, edit links, sidebar, custom CSS, components, plugins, content loaders, and schemas are relevant to this repo's docs site architecture.

## Artifact Freshness

`config/docs-artifact-registry.json` tracks selected generated docs artifacts and validation commands, but the docs generator writes more surfaces than the registry currently enumerates. README freshness has a non-mutating check via `uv run wagents readme --check`; docs generation does not yet have an equivalent `wagents docs generate --check` command.

Read-only research found generated site data and catalog counts aligned with authoring sources (363 skills in index: 56 custom + 307 curated-external). Compose coverage manifest (2026-06-23) reports 98.2% composed (381/388); five missing hook pages are Cursor hooks present in registry but without composed MDX.

Stale hand-maintained gap persists: `docs/src/content/docs/mcp/index.mdx` badge still disagrees with `mcp.json`/generated counts. There is no `wagents docs generate --check` equivalent to `readme --check` or `catalog index --check`. `config/docs-artifact-registry.json` lists only five generated artifacts though the generator emits more surfaces.

## Evidence

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| Docs generation is driven by `wagents docs generate`. | `kb/raw/sources/docs-site-architecture.md`; `kb/raw/sources/wagents-internals.md` | raw source notes | Local implementation is authoritative. |
| Starlight config lives in Astro config and uses `starlight()`. | `kb/raw/sources/docs-site-architecture.md`; `kb/raw/sources/external-tooling-docs.md` | external source notes | Official Starlight docs verified. |
| Generated docs are source-derived surfaces. | `kb/raw/sources/docs-site-architecture.md`; `kb/raw/sources/config-registries-and-sync.md` | raw source notes | Update via generator, not generic note edits. |
| Docs artifact registry, freshness checks, and MCP count drift need separate attention from ordinary docs generation. | `kb/raw/sources/docs-artifact-freshness.md` | raw source note | Autoresearch finding; full docs build not run. |

## Related

- [[wagents-cli-and-automation]]
- [[canonical-generated-surfaces]]
- [[known-risks-and-open-gaps]]
- [[validation-and-test-coverage]]
