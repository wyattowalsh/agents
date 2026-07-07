# Tasks

## Implementation

- [x] Verify docs package freshness with `npm-check-updates` and package-manager version probes.
- [x] Add direct `esbuild` dev dependency required for Vite 8 `build.cssMinify: 'esbuild'`.
- [x] Switch docs build CSS minification from disabled to `esbuild`.
- [x] Keep `SkipLink` as a Starlight body override, not a `Head` child.
- [x] Server-render install-script command groups and keep generated JSON hydration.
- [x] Generate the install page with `skillInstallScripts` from generated site data.
- [x] Add list semantics to the homepage projection visual.
- [x] Preserve generated report and curated research-install suppression tests.
- [ ] Regenerate docs and README from source.

## Verification

- [x] `pnpm dlx npm-check-updates --packageFile package.json --format group --target latest`
- [x] `pnpm view esbuild version`
- [x] `pnpm dlx pnpm@11.10.0 --version`
- [ ] `uv run pytest -q tests/test_docs.py tests/test_docs_reports.py tests/test_rendering.py tests/test_candidate_corpus.py tests/test_pentest_skill_scripts.py`
- [ ] `uv run wagents validate`
- [ ] `uv run wagents openspec validate`
- [ ] `uv run wagents docs generate --check`
- [ ] `uv run wagents catalog index --check --format json`
- [ ] `uv run wagents readme --check --format json`
- [ ] `uv run wagents skills sync --dry-run`
- [ ] `pnpm dlx pnpm@11.10.0 --dir docs exec astro check`
- [ ] `mise exec node@24 -- pnpm dlx pnpm@11.10.0 --dir docs build`
- [ ] Built HTML probes for skip link placement, no-JS install/catalog content, stale research command suppression, and emitted OG images.
