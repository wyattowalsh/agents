# Proposal: Harden docs site findings closure

## Problem

The docs site findings span build configuration, package freshness, Starlight
component overrides, no-JS command surfaces, generated report semantics, and
curated external catalog rendering. Treating these as isolated patches risks
shipping stale generated output, invalid accessibility markup, or a broad
dependency upgrade without proof that the latest docs stack still builds.

## Intent

Close the findings as one docs-hardening lane: use latest working docs package
versions, keep Vite CSS minification enabled through `esbuild`, preserve the
Astro/Starlight/astro-og-canvas contracts verified by current docs, keep the
Starlight docs static by default while admin/API routes opt into on-demand
rendering, pre-render install commands before client hydration, keep generated
catalog research from overriding canonical install commands, and regenerate
public docs from source.

## Scope

- Docs dependency/toolchain validation for latest package versions.
- Vite build CSS minifier policy for the Astro docs app.
- Starlight `Head` and `SkipLink` override placement.
- Server-rendered install-script command sections with JSON hydration fallback.
- Homepage projection accessibility semantics.
- Docs report and curated catalog rendering regression coverage.
- Generated docs, README, catalog index, and build validation.

## Out Of Scope

- Live skill installs or `wagents skills sync --apply`.
- Publishing, tagging, committing, pushing, branch switching, or worktree changes.
- Promoting candidate-corpus rows to installable curated external skills.
- Reworking unrelated pentest, MCPHub, hook, or runtime-policy dirty surfaces.
