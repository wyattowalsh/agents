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

CI runs seven jobs on push/PR to `main`: lint, typecheck, test, validate, apm, wagents-wheel, and docs. The validate job runs `wagents validate`, `wagents readme --check`, `wagents apm materialize --check`, `wagents apm doctor`, a curated pytest slice (catalog/authoring/APM parity), `wagents openspec validate`, `wagents skills sync --dry-run`, and `wagents catalog index --check`.

The docs job runs `wagents docs generate --no-installed`, catalog index check, `wagents docs compose --check-composed --min-pct 100`, docs lint, Astro check, and `pnpm build`. Release-skills validates on every PR with strict skill audit + full pytest; package-and-release runs only on version tags.

Pre-commit adds path-filtered hooks for validate, apm check/doctor, openspec validate, catalog index check, and docs build check.

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