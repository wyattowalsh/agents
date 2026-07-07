# Tasks

## Implementation

- [x] Verify docs package freshness with `npm-check-updates` and package-manager version probes.
- [x] Add direct `esbuild` dev dependency required for Vite 8 `build.cssMinify: 'esbuild'`.
- [x] Switch docs build CSS minification from disabled to `esbuild`.
- [x] Keep Starlight docs static by default while admin/API routes opt into on-demand rendering.
- [x] Keep `SkipLink` as a Starlight body override, not a `Head` child.
- [x] Server-render install-script command groups and keep generated JSON hydration.
- [x] Generate the install page with `skillInstallScripts` from generated site data.
- [x] Add list semantics to the homepage projection visual.
- [x] Restore docs build cleanup for stale `dist`, `.astro`, and Vercel output artifacts.
- [x] Add a slim generated catalog browser index for external skill grid hydration.
- [x] Add schema and stale-contract checks for the catalog browser index.
- [x] Preserve generated report and curated research-install suppression tests.
- [x] Regenerate docs and README from source.

## Verification

- [x] `pnpm dlx npm-check-updates --packageFile docs/package.json --format group --target latest`
- [x] `pnpm view esbuild version`
- [x] `pnpm dlx pnpm@11.10.0 --version`
- [x] `uv run pytest -q tests/test_docs.py tests/test_docs_reports.py tests/test_rendering.py tests/test_candidate_corpus.py tests/test_pentest_skill_scripts.py`
- [x] `uv run wagents validate`
- [ ] `uv run wagents openspec validate`
- [x] `npx -y @fission-ai/openspec@latest validate harden-docs-site-findings-jul2026 --strict --json`
- [x] `uv run wagents docs generate --no-installed --check`
- [x] `uv run wagents catalog index --check --format json`
- [x] `uv run wagents readme --check --format json`
- [x] `uv run wagents skills sync --dry-run`
- [x] `mise exec node@24 -- pnpm dlx pnpm@11.10.0 --dir docs exec astro check`
- [x] `(cd docs && ASTRO_TELEMETRY_DISABLED=1 NODE_OPTIONS=--max-old-space-size=4096 pnpm exec astro build --force)`
- [x] Built HTML probes for no-JS install/catalog content, candidate-corpus HTML retention, and emitted OG image suppression/retention.
- [x] Focused catalog browser index tests for schema, bounded payload, stale detection, and display-only fields.
- [x] Stale docs output cleanup test for `dist`, `.astro`, and `.vercel/output`.

`uv run wagents openspec validate` remains unchecked because the all-change sweep still fails on unrelated pre-existing changes `add-open-websearch-mcp-skill` and `replace-package-version-check-mcp`, each with no parsed OpenSpec deltas. The targeted docs hardening change validates strictly.
