---
title: Harness Fixture Capture W01
tags:
  - kb
  - raw
  - harness
  - fixtures
aliases:
  - Harness fixture capture 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave01-partials-2026-06-25
---

# Harness Fixture Capture W01

Read-only harness fixture support snapshot on 2026-06-25.

## Manifest summary (`planning/manifests/harness-fixture-support.json`)

| Metric | Value |
|--------|-------|
| Harness records | 19 |
| `fixture-executable` | 12 |
| `rollback_coverage: present` | 8 |
| `rollback_coverage: planned` | 8 |

## Executable rollback pytest surface

`tests/test_harness_rollback_fixtures.py` — 8 collected tests (Cursor home MCP merge, Cursor CLI idempotency, Grok merge preservation, config-drop negatives, symlink `.bak` paths).

## Docs compose (related fixture gate)

397/397 composed (100%) including 22 hook pages — prior Cursor hook compose gap closed.

## Remaining plan-only harnesses (examples)

`claude-desktop`, `cherry-studio`, `chatgpt`, `github-copilot-web` — fixture-plan-only or docs-ledger-required per manifest rows.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Fixture tiers | `planning/manifests/harness-fixture-support.json` | canonical repo path |
| Rollback tests | `tests/test_harness_rollback_fixtures.py` | canonical repo path |
| Compose gate | `wagents docs compose --check-composed` | tool capture |