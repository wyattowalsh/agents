# Validation Matrix

| Gate | Command / Probe | Purpose |
| --- | --- | --- |
| Package freshness | `pnpm dlx npm-check-updates --packageFile package.json --format group --target latest` | Verify docs package ranges are current. |
| Toolchain | `pnpm dlx pnpm@11.10.0 --version` | Verify the package-manager version declared by the docs app is runnable. |
| CSS minifier dep | `pnpm view esbuild version` | Verify the direct Vite `cssMinify: 'esbuild'` dependency target. |
| Unit tests | `uv run pytest -q tests/test_docs.py tests/test_docs_reports.py tests/test_rendering.py tests/test_candidate_corpus.py tests/test_pentest_skill_scripts.py` | Cover generator, report, rendering, corpus, and adjacent pentest regressions. |
| Repo validation | `uv run wagents validate` | Validate repo-owned assets and docs/catalog invariants. |
| OpenSpec | `uv run wagents openspec validate` | Validate change/spec metadata where unrelated changes permit it. |
| Generation check | `uv run wagents docs generate --check` | Ensure generated docs are source-current. |
| Catalog check | `uv run wagents catalog index --check --format json` | Ensure catalog index is source-current. |
| README check | `uv run wagents readme --check --format json` | Ensure README was regenerated from source. |
| Sync preview | `uv run wagents skills sync --dry-run` | Verify no unintended live install commands. |
| Astro typecheck | `pnpm dlx pnpm@11.10.0 --dir docs exec astro check` | Verify Astro/Starlight component and content contracts. |
| Production build | `mise exec node@24 -- pnpm dlx pnpm@11.10.0 --dir docs build` | Verify Vercel-targeted production output with CSS minification enabled. |
| Static probes | built HTML `rg` checks | Verify skip link, no-JS fallbacks, stale research suppression, and OG output. |
