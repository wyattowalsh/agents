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
updated: 2026-07-01
source_count: 6
---

# CI And Release Workflows

## Summary

GitHub Actions and pre-commit enforce validation, docs freshness, catalog parity, and release packaging. CI jobs bootstrap through composite `.github/actions/setup-uv`, then run `uv run wagents ...` gates. The justfile provides local shorthand equivalents plus `just ci-check` (actionlint + workflow-analyzer).

## Why it matters

- KB claims about repo health should cite which CI job actually proves them.
- The validate job is lighter than release-skills (strict audit + full pytest on PRs).
- Docs compose coverage (`--check-composed --min-pct 100`) gates only in the docs job and pre-commit, not the core validate job.

## Current shape

| Workflow | Trigger | Notable gates |
|----------|---------|---------------|
| `ci.yml` | push/PR main | lint, ty, pytest, validate slice, apm, wagents-wheel, docs build (SHA-pinned actions, timeouts, least-privilege permissions) |
| `ideas-quality-gates.yml` | push/PR/dispatch | eval validate, eval adequacy, hooks validate (interim until ci.yml rebase) |
| `maintenance-freshness.yml` | weekly schedule | readme/docs/catalog freshness checks |
| `reusable-validate.yml` | workflow_call | lint + validate + SARIF + curated pytest subset |
| `install-smoke-phase3.yml` | workflow_dispatch | INSTALL_SMOKE=1 matrix (phase 3 only) |
| `dependency-review.yml` | PR | dependency-review-action |

**Validate job sequence:** `wagents validate` → `readme --check` → `apm materialize --check` → `apm doctor` → curated pytest → `openspec validate` → `skills sync --dry-run` → `catalog index --check`. Use `wagents validate --format sarif` for IDE/CI SARIF consumers.

**Local verify recipes:** `just verify-fast`, `just verify-docs`, `just verify-all` (W1).

**Path-aware pytest:** `uv run python scripts/path_aware_pytest.py` selects tests from git diff (W11).

**Docs job sequence:** `docs generate --no-installed` → catalog index check → `docs compose --check-composed --min-pct 100` → Astro check → build.

## Constraints and edge cases

- CI validate does not run full pytest or strict skill audit (release-skills does on PR).
- `wagents docs lint` in CI uses `|| true` (non-blocking).
- No CI invocation of `scripts/validate_codex_config.py` as of 2026-06-23.
- Workflow hardening regression tests live in `tests/test_github_workflows.py`; Dependabot updates action SHAs via `.github/dependabot.yml`.

## 2026-06-25 refresh (Wave 11)

Fresh capture confirms seven CI jobs with explicit command pairing: `lint` runs Ruff check + format check; `typecheck` runs `ty check`; `test` runs full pytest with coverage; `validate` runs the wagents/openspec/catalog slice plus a six-file curated pytest subset (not the full suite).

## Provenance

| Claim or section | Raw or canonical material | Notes |
|------------------|---------------------------|-------|
| Job definitions and command lists | `kb/raw/sources/ci-release-workflows-source.md` | Primary summary |
| Fresh job/command table | `kb/raw/captures/ci-workflow-jobs-capture-w11.md` | Wave 11 read-only capture |
| Pre-commit hook inventory (10 local hooks) | `kb/raw/captures/pre-commit-hooks-capture-w14.md` | Wave 14 path-filtered hooks |
| Release-skills strict audit + full pytest + tag ZIP release | `kb/raw/captures/release-skills-workflow-capture-w15.md` | Wave 15 pass 2 |
| Developer command aliases | `justfile` | justfile |
| Validation collector details | `kb/raw/sources/scripts-validation-tooling-source.md` | Scripts layer |

## Related wiki pages

- [[validation-and-test-coverage]]
- [[developer-commands]]
- [[docs-generation-and-site]]

## Open questions

- Whether hook/eval validate should become CI gates with `--check` semantics similar to catalog index.