---
title: CI And Release Workflows
tags:
  - kb
  - source
  - ci
aliases:
  - CI workflows source
kind: source-summary
status: active
updated: 2026-06-23
source_count: 1
---

# CI And Release Workflows

## Source Record

| Field | Value |
|-------|-------|
| source_id | `ci-release-workflows` |
| original_location | `.github/workflows/ci.yml`; `.github/workflows/release-skills.yml`; `.pre-commit-config.yaml`; `Makefile` |
| raw_path | `kb/raw/sources/ci-release-workflows-source.md` |
| capture_method | repo-local pointer summary from read-only research |
| captured_at | 2026-06-23 |
| size_bytes | pointer summary only |
| checksum | not captured |
| license_or_access_notes | repo-local canonical material |
| intended_wiki_coverage | [[ci-and-release-workflows]], [[validation-and-test-coverage]], [[developer-commands]] |

## Summary

CI runs seven parallel jobs on push/PR to `main`: lint, typecheck, test, validate, apm, wagents-wheel, and docs. Jobs bootstrap via composite action `.github/actions/setup-uv` (checkout, SHA-pinned `setup-uv` with cache, `uv sync`). Workflows use top-level `permissions: {}`, per-job least privilege, job `timeout-minutes`, SHA-pinned third-party actions, and PR concurrency (`cancel-in-progress: true`; release workflow cancels only on PRs).

The validate job runs `wagents validate`, `wagents readme --check`, `wagents apm materialize --check`, `wagents apm doctor`, a curated pytest slice (catalog/authoring/APM parity), `wagents openspec validate`, `wagents skills sync --dry-run`, and `wagents catalog index --check`.

The docs job runs `wagents docs generate --no-installed`, catalog index check, `wagents docs compose --check-composed --min-pct 100`, non-blocking `wagents docs lint || true`, Astro check, and `pnpm build`. Release-skills validates on every PR with strict skill audit + full pytest; package-and-release runs only on version tags.

Pre-commit adds path-filtered hooks for validate, apm check/doctor, openspec validate, catalog index check, docs build check, and `actionlint` on `.github/workflows/`. Local workflow lint: `make ci-check`. Dependabot watches `github-actions` weekly. Regression tests: `tests/test_github_workflows.py`.

## Provenance

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| CI job structure and commands. | `.github/workflows/ci.yml` | canonical material | Seven jobs |
| Release workflow gates. | `.github/workflows/release-skills.yml` | canonical material | PR validate + tag release |
| Pre-commit validation hooks. | `.pre-commit-config.yaml` | canonical material | Path-filtered |
| Makefile provides local shorthand targets. | `Makefile` | canonical material | CI uses `uv run` directly |

## Planned wiki coverage

| Topic | Status |
|-------|--------|
| [[ci-and-release-workflows]] | primary synthesis |
| [[validation-and-test-coverage]] | cross-link |