---
title: CI And Release Workflows
tags:
  - kb
  - ci
  - release
aliases:
  - CI pipelines
kind: concept
status: active
updated: 2026-06-23
source_count: 2
---

# CI And Release Workflows

## Summary

GitHub Actions and pre-commit enforce validation, docs freshness, catalog parity, and release packaging. CI uses `uv run wagents ...` directly; the Makefile provides local shorthand equivalents.

## Why it matters

- KB claims about repo health should cite which CI job actually proves them.
- The validate job is lighter than release-skills (strict audit + full pytest on PRs).
- Docs compose coverage (`--check-composed --min-pct 100`) gates only in the docs job and pre-commit, not the core validate job.

## Current shape

| Workflow | Trigger | Notable gates |
|----------|---------|---------------|
| `ci.yml` | push/PR main | lint, ty, pytest, validate slice, apm, wagents-wheel, docs build |
| `release-skills.yml` | PR + version tags | strict skill audit, full pytest; zip release on tags |

**Validate job sequence:** `wagents validate` → `readme --check` → `apm materialize --check` → `apm doctor` → curated pytest → `openspec validate` → `skills sync --dry-run` → `catalog index --check`.

**Docs job sequence:** `docs generate --no-installed` → catalog index check → `docs compose --check-composed --min-pct 100` → Astro check → build.

## Constraints and edge cases

- CI validate does not run full pytest or strict skill audit (release-skills does on PR).
- `wagents docs lint` in CI uses `|| true` (non-blocking).
- No CI invocation of `scripts/validate_codex_config.py` as of 2026-06-23.

## Provenance

| Claim or section | Raw or canonical material | Notes |
|------------------|---------------------------|-------|
| Job definitions and command lists | `kb/raw/sources/ci-release-workflows-source.md` | Primary |
| Developer command aliases | `kb/raw/sources/pyproject-and-makefile.md` | Makefile |
| Validation collector details | `kb/raw/sources/scripts-validation-tooling-source.md` | Scripts layer |

## Related wiki pages

- [[validation-and-test-coverage]]
- [[developer-commands]]
- [[docs-generation-and-site]]

## Open questions

- Whether hook/eval validate should become CI gates with `--check` semantics similar to catalog index.