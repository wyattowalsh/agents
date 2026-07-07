# Tasks

- [x] Audit requested plugins for package availability, peer compatibility, component override ownership, route/output behavior, and content-source requirements.
- [x] Install peer-compatible packages that are enabled or directly used by the docs site.
- [x] Remove peer-conflicting or unused direct dependencies from the attempted install set.
- [x] Configure compatible Astro integrations and Starlight plugins in `docs/astro.config.mjs`.
- [x] Extend Starlight frontmatter schema for `starlight-tags` while preserving site-graph schema.
- [x] Add a minimal tags taxonomy and proof/download fixture.
- [x] Add a hand-maintained compatibility ledger and proof page under harness config.
- [x] Regenerate generated docs/sidebar surfaces.
- [x] Run validation gates and record blockers.

## Validation Notes

- `uv run wagents docs generate --no-installed`: passed; regenerated 714 pages, indexes, and sidebar.
- `pnpm peers check`: passed with no peer dependency issues.
- `pnpm exec astro check`: passed with 0 errors, 0 warnings, and 0 hints.
- `public/generated-reports/docs-link-check.json`: `broken_count` is 0 across 1172 scanned pages.
- `uv run wagents openspec validate`: `integrate-starlight-plugin-stack` is valid, but repo-wide OpenSpec validation is blocked by unrelated existing changes `add-open-websearch-mcp` and `replace-package-version-check-mcp` having no deltas.
- `pnpm exec astro build`: blocked after generated catalog refresh. Latest clean Node 24 build with `dist` and `.astro` removed plus `NODE_OPTIONS=--max-old-space-size=16384` exited 143 during Vite server-entrypoint bundling after the Mermaid transform; no successful build completion was emitted.
