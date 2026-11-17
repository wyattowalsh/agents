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
- `pnpm exec astro build --force`: passed after a clean `dist`, `.astro`, and `.vercel/output` rebuild with `NODE_OPTIONS=--max-old-space-size=6144`; Pagefind found 1176 HTML files, internal links were valid, sitemap/sitegraph outputs were emitted, and Astro completed with `Server built in 2m 36s` / `Complete!`.
- Build warning retained: local Node.js 26 is not a supported Vercel Serverless Functions runtime; the Vercel adapter reports Node.js 24 will be used for deployment.
