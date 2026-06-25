---
title: Wagents Doctor Checks Capture W27
tags:
  - kb
  - raw
  - wagents
aliases:
  - Wagents doctor checks 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave27-pass5-2026-06-25
---

# Wagents Doctor Checks Capture W27

Command-backed snapshot of `uv run wagents doctor --format json` on 2026-06-25.

## Summary

- **ok**: true
- **total checks**: 18 (17 ok, 1 warn, 0 fail)

## Check IDs

| Check | Typical status |
|-------|----------------|
| python-version | ok (requires >=3.13) |
| uv, node, npx, pnpm | PATH presence |
| node-version | semver vs `docs/package.json` engines |
| pnpm-version | pin vs `packageManager` field |
| docs-deps | node_modules + lock presence |
| pre-commit | hook env |
| playwright-python / playwright-browsers | browser test deps |
| wagents-install-mode | uv tool vs editable |
| wagents-binary | CLI on PATH |
| repo-discovery | WAGENTS_REPO_ROOT / cwd |
| telemetry | opt-in posture |
| python-tooling-config | pyproject tooling sections |
| ruff-tooling / ty-tooling | linter/type checker bins |

## Related commands

- `wagents self doctor` — wagents package install health
- `wagents grok doctor --format json` — Grok-specific (separate sub-app)

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Check list | `uv run wagents doctor --format json` | tool output |
| Implementation | `wagents/cli.py` `_collect_doctor_checks` | canonical repo |