---
title: Docs Generate Check Capture W06
tags:
  - kb
  - raw
  - docs
aliases:
  - Docs generate check 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave06-docs-authoring-2026-06-25
---

# Docs Generate Check Capture W06

Freshness gates for docs generation on 2026-06-25.

## Captured Facts

| Check | Result | Evidence |
|-------|--------|----------|
| `wagents docs generate --no-installed --check` | wired in CI | `.github/workflows/ci.yml` |
| Prior session check | up to date | `kb/raw/captures/wagents-docs-cli-capture-w02.md` |
| Compose gate | 100% minimum | same workflow + `docs-freshness-capture-w01` |
| Catalog index check | `wagents catalog index --check` per authoring policy | `skills-catalog-authoring-lifecycle-source` |

## Remaining hand-maintained drift

MCP landing badge (15 vs 33 servers) tracked in `docs-freshness-capture-w01`; not a generator defect.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| CI generate --check | `.github/workflows/ci.yml` | canonical repo path |
| CLI check behavior | `wagents/docs.py` | canonical repo path |