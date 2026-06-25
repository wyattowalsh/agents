---
title: Release Skills Workflow Capture W15
tags:
  - kb
  - raw
  - release
aliases:
  - Release skills 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave15-pass2-2026-06-25
---

# Release Skills Workflow Capture W15

Read-only capture from `.github/workflows/release-skills.yml` on 2026-06-25.

## Triggers

| Event | Behavior |
|-------|----------|
| `pull_request` → `main` | Validate job only |
| `push` tag `v*.*.*` | Validate + package-and-release |

PR concurrency: `cancel-in-progress: true`; tag pushes do not cancel.

## Validate job (stricter than `ci.yml` validate)

| Step | Command |
|------|---------|
| Validate assets | `uv run wagents validate` |
| Strict skill audit | `uv run python skills/skill-creator/scripts/audit.py --all --strict` |
| Full pytest | `uv run pytest` |
| Lint | `uv run ruff check` |
| Format | `uv run ruff format --check` |
| Typecheck | `uv run ty check --output-format github --no-progress` |

## package-and-release job (tags only)

`needs: validate`; `contents: write`; runs `uv run wagents package --all --output dist/`; verifies `dist/manifest.json` and at least one `.zip`; creates GitHub Release.

## vs CI validate job

Release-skills adds **strict audit** + **full pytest** + ruff/ty; CI validate uses curated pytest slice and omits strict audit.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Workflow steps | `.github/workflows/release-skills.yml` | canonical repo |
| CI compare | `kb/raw/captures/ci-workflow-jobs-capture-w11.md` | raw capture |