---
title: Pre Commit Hooks Capture W14
tags:
  - kb
  - raw
  - pre-commit
aliases:
  - Pre-commit hooks 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave14-gap-sweep-2026-06-25
---

# Pre Commit Hooks Capture W14

Read-only capture from `.pre-commit-config.yaml` on 2026-06-25. Ten local hooks; path-filtered triggers.

| Hook id | Entry | File filter |
|---------|-------|-------------|
| `ruff` | `uv run ruff check` | `\.py$` |
| `ruff-format` | `uv run ruff format --check` | `\.py$` |
| `ty` | `uv run ty check` | `\.py$` |
| `wagents-validate` | `uv run wagents validate` | `skills/`, `agents/` |
| `apm-materialize-check` | `wagents apm materialize --check` | agents/instructions/apm paths |
| `apm-doctor` | `wagents apm doctor` | apm.yml, .apm/, opencode.json |
| `openspec-validate` | `wagents openspec validate` | `openspec/` |
| `catalog-index-check` | `wagents catalog index --check` | authoring MDX + SKILL.md |
| `docs-build-check` | `wagents docs build` | docs/skills/agents/mcp paths |
| `actionlint` | `actionlint` | `.github/workflows/*.yml` |

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Hook table | `.pre-commit-config.yaml` | canonical repo |
| CI overlap | `kb/raw/captures/ci-workflow-jobs-capture-w11.md` | raw capture |