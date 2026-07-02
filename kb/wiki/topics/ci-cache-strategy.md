---
title: CI Cache Strategy
tags:
  - kb
  - ci
  - cache
aliases:
  - GitHub Actions cache
kind: concept
status: active
updated: 2026-07-01
source_count: 3
---

# CI Cache Strategy

## Summary

This repository relies on **uv** workspace caching via the composite `.github/actions/setup-uv` action (`astral-sh/setup-uv@v5` with `enable-cache: true`). Python dependencies are restored before `uv sync` on every CI job. Docs builds use pnpm inside `docs/` with lockfile pinning; no separate GitHub Actions cache entry is required for routine validate jobs.

## Layers

| Layer | Owner | Cache key driver | Invalidates when |
|-------|-------|------------------|------------------|
| uv Python deps | `setup-uv` | `uv.lock` + Python version | Lockfile or Python pin changes |
| pnpm docs deps | `docs/pnpm-lock.yaml` | lock hash in docs job | docs lockfile changes |
| pytest selection | `scripts/path_aware_pytest.py` | git diff path map | N/A (no persistent cache) |

## Local parity

- Use `uv sync` once per clone; subsequent `uv run` reuses `.venv`.
- For docs: `wagents docs init` then `pnpm install` in `docs/` (lockfile-driven).
- Fast inner loop: `just verify-fast` or `uv run python scripts/path_aware_pytest.py --list-only`.

## Maintenance workflow

The scheduled `maintenance-freshness.yml` workflow re-runs freshness `--check` gates weekly. Stale generated artifacts fail there without blocking every PR push.

## Related

- [[ci-and-release-workflows]]
- [[developer-commands]]
- [[validation-and-test-coverage]]
