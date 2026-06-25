---
title: OpenSpec Validate Snapshot Capture W16
tags:
  - kb
  - raw
  - openspec
aliases:
  - OpenSpec validate 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave16-pass2-2026-06-25
---

# OpenSpec Validate Snapshot Capture W16

Tool capture from `uv run wagents openspec validate --format json` on 2026-06-25.

## Result

| Field | Value |
|-------|-------|
| `ok` | `true` |
| Active changes checked | present in validate payload |
| Specs checked | present in validate payload |

Command exit code: **0**. CI validate job and pre-commit `openspec-validate` hook both invoke `wagents openspec validate`.

## Interpretation

OpenSpec gate is green for this snapshot; active/archive counts may drift between captures — use [[openspec-change-archive-status]] for directory inventory and this capture for validate pass/fail only.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| JSON ok flag | `uv run wagents openspec validate --format json` | tool capture |
| Active inventory | `kb/raw/captures/openspec-active-changes-capture-w04.md` | raw capture |