---
title: Wagents Eval CLI Capture W02
tags:
  - kb
  - raw
  - wagents
  - evals
aliases:
  - Wagents eval CLI 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave02-wagents-2026-06-25
---

# Wagents Eval CLI Capture W02

Read-only capture from `wagents eval` subcommands, `wagents/eval_adequacy.py`, and JSON CLI runs on 2026-06-25. Not an instruction source.

## Captured Facts

| Fact | Value | Source |
|------|-------|--------|
| Typer sub-app | `eval_app` mounted as `wagents eval` | `wagents/cli.py` |
| Subcommands (4) | `list`, `validate`, `coverage`, `adequacy` | `wagents eval --help` |
| Manifest scan path | `skills/*/evals/*.json` via `_collect_evals()` | `cli.py` |
| Validate delegation | `skills/skill-creator/scripts/asset_toolkit/validate_evals.py` | `eval_validate()` |
| Coverage semantics | compares skills with `SKILL.md` against per-skill eval case counts | `eval_coverage()` |
| Adequacy engine | structural E3/E4 grader in `wagents/eval_adequacy.py`; `--strict` exits 1 on R3/R4 without E4 | `eval_adequacy()` |
| 2026-06-25 list | 56 skills, 791 eval cases | `wagents eval list --format json` |
| 2026-06-25 coverage | 56/56 skills `has_evals: true` | `wagents eval coverage --format json` |
| 2026-06-25 adequacy | `count: 56`, `failing_strict: []` (0 needs_e4) | `wagents eval adequacy --format json` |
| Related hooks surface | `wagents hooks list` reports 40 hooks; `hooks validate` delegates to `validate_hooks.py` | `cli.py` hooks_app |

## Quoted CLI excerpt

> `"count": 56, "eval_count": 791` — full-repo eval list.

> `"failing_strict": []` — adequacy strict gate clean for high-risk tier.

## Interpretation

Eval CLI combines filesystem inventory (`list`, `coverage`), schema validation (`validate`), and risk-adjusted structural adequacy (`adequacy`). Live LLM eval execution is out of scope for these commands; they enforce manifest presence and E3/E4 signal structure. Hooks commands share the control-plane namespace but enforce portable hook registry rules separately.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Subcommand wiring | `wagents/cli.py` | canonical repo path |
| Adequacy logic | `wagents/eval_adequacy.py` | canonical repo path |
| JSON metrics | `wagents eval list/coverage/adequacy --format json`, `wagents hooks list --format json` | tool capture |