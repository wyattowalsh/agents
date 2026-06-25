---
title: Skill Eval Inventory Capture W01
tags:
  - kb
  - raw
  - inventory
  - evals
aliases:
  - Eval adequacy capture 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave01-partials-2026-06-25
---

# Skill Eval Inventory Capture W01

Read-only capture from `uv run wagents eval adequacy --format json` on 2026-06-25. Not an instruction source.

## Captured Facts

| Metric | Value | Command |
|--------|-------|---------|
| Skills with eval manifests | 56/56 | `wagents eval adequacy` |
| High-risk skills (R3/R4) | 14 | same |
| Skills flagged `needs_e4` | 0 | same |
| Structural adequacy at E4 for high-risk set | 14/14 | JSON `adequacy` field |

## Quoted CLI excerpt

> `"count": 56` — all repo skills returned in adequacy report.

> High-risk examples include `email-whiz` (R4, adequacy E4), `mcp-creator` (R4, E4), chrome-devtools family (R3, E4).

## Interpretation

Manifest presence is saturated; structural adequacy CLI reports no remaining `needs_e4` skills. Live LLM eval execution and per-skill boundary depth remain separate from this structural gate.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Adequacy counts | `wagents eval adequacy --format json` | tool capture |
| Risk tiers | `wagents/eval_adequacy.py` | canonical repo path |