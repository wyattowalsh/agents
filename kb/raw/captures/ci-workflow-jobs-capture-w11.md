---
title: CI Workflow Jobs Capture W11
tags:
  - kb
  - raw
  - ci
aliases:
  - CI jobs 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave11-gap-sweep-2026-06-25
---

# CI Workflow Jobs Capture W11

Fresh read-only capture from `.github/workflows/ci.yml` and `.github/workflows/release-skills.yml` on 2026-06-25. Supersedes stale job lists in `ci-release-workflows-source.md` where they diverge.

## `ci.yml` jobs (7)

| Job | Timeout | Primary commands |
|-----|---------|------------------|
| `lint` | 10m | `uv run ruff check`; `uv run ruff format --check` |
| `typecheck` | 10m | `uv run ty check --output-format github --no-progress` |
| `test` | 15m | `uv run pytest --cov=wagents --cov-report=term-missing` |
| `validate` | 25m | `wagents validate`; `readme --check`; `apm materialize --check`; `apm doctor`; curated pytest slice; `openspec validate`; `skills sync --dry-run`; `catalog index --check` |
| `apm` | 15m | `apm audit --ci --no-drift`; conditional frozen `apm install` |
| `wagents-wheel` | 15m | `uv build`; `uv tool install` wheel; `wagents self doctor`; `wagents validate` |
| `docs` | 30m | `wagents docs generate --no-installed`; catalog index check; `docs compose --check-composed --min-pct 100`; `docs lint \|\| true`; Astro check; `pnpm build` |

Shared bootstrap: composite `.github/actions/setup-uv`. Top-level `permissions: {}` with per-job `contents: read`. PR concurrency `cancel-in-progress: true`.

## Validate job curated pytest slice (explicit paths)

```
tests/test_skills_catalog_schemas.py
tests/test_catalog_index_parity.py
tests/test_skill_index.py
tests/test_authoring_sync.py
tests/test_apm_materialize.py
tests/test_wagents_self.py
```

## Interpretation

- Full pytest coverage is **not** in the validate job; `test` job runs full suite with coverage.
- Docs compose 100% gate is docs-job only (not validate job).
- `wagents docs lint` remains non-blocking (`|| true`).

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Job table | `.github/workflows/ci.yml` | canonical repo |
| Prior summary | `kb/raw/sources/ci-release-workflows-source.md` | raw source note (2026-06-23) |