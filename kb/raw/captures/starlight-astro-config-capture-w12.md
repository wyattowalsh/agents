---
title: Starlight Astro Config Capture W12
tags:
  - kb
  - raw
  - docs
  - starlight
aliases:
  - Starlight config 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave12-gap-sweep-2026-06-25
---

# Starlight Astro Config Capture W12

Read-only capture from `docs/astro.config.mjs` on 2026-06-25. Aligns with upstream Starlight `starlight()` integration documented in `external-tooling-docs`.

## Integration stack

| Piece | Config |
|-------|--------|
| Framework | Astro `defineConfig` with `output: 'server'`, Vercel adapter |
| Starlight | `starlight({ title, description, sidebar: generatedSidebar, … })` |
| Plugins | `starlightThemeBlack`, `starlightLinksValidator`, `starlightLlmsTxt` (`rawContent: true`) |
| Generated inputs | `./src/generated-sidebar.mjs`, `./src/generated-site-data.mjs` |
| CSS | Tailwind via Vite plugin + token/base/component stylesheets |

## CI/docs gate pairing

Docs job runs `wagents docs generate --no-installed` before Astro check/build. Starlight sidebar is generator-owned (`wagents docs generate`), not hand-edited in committed pages.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Plugin array and options | `docs/astro.config.mjs` | canonical repo |
| Upstream Starlight model | `https://starlight.astro.build/reference/configuration/` | external docs |
| Prior architecture | `kb/raw/sources/docs-site-architecture.md` | raw source note |