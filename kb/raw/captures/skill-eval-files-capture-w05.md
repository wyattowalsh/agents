---
title: Skill Eval Files Capture W05
tags:
  - kb
  - raw
  - evals
  - skills
aliases:
  - Skill eval files inventory 2026-06-25 wave05
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave05-hooks-tests-2026-06-25
---

# Skill Eval Files Capture W05

Read-only inventory of `skills/*/evals/` layout and `wagents eval` CLI counts on 2026-06-25 (Wave 05).

## Manifest presence

| Metric | Value |
|--------|-------|
| Skills under `skills/` | 56 |
| Canonical `evals/evals.json` manifests | 56/56 (100%) |
| Cases summed from manifests only | 602 |
| Legacy `evals/*.json` (non-manifest) | 189 files |
| `wagents eval list` total cases | 791 |

## Count reconciliation

`wagents eval list` scans **all** `skills/*/evals/*.json` via `_collect_evals()` in `wagents/cli.py`. Each legacy per-case JSON file counts as one eval entry in addition to manifest cases:

```
602 (manifest cases) + 189 (legacy files) = 791 (CLI eval_count)
```

Adequacy (`wagents eval adequacy`) grades canonical manifest structure per skill; it does not execute legacy file inventory separately.

## CLI snapshots

```
uv run wagents eval list --format json
→ count: 56 skills, eval_count: 791

uv run wagents eval adequacy --strict --format json
→ count: 56, failing_strict: [], high_risk: 14 skills
```

## Case distribution (manifest-only)

| Stat | Value |
|------|-------|
| Median cases per skill | 7 |
| Skills with ≥20 manifest cases | 8 |
| Skills with <5 manifest cases | 2 |

### Top 5 by manifest case count

| Skill | Manifest cases |
|-------|----------------|
| harness-master | 68 |
| nerdbot | 50 |
| docs-steward | 48 |
| new-project | 40 |
| design | 39 |

### Thin manifests (<5 cases)

| Skill | Manifest cases |
|-------|----------------|
| i18n-localization | 4 |
| skill-router | 3 |

## skill-creator regression anchor

`test_eval_cli.py::test_skill_creator_real_repo_uses_single_consolidated_manifest` asserts `skills/skill-creator/evals/` contains only `evals.json` (no stray legacy files) and ≥27 named case ids with non-empty `prompt` / `expected_output`.

## Interpretation

100% manifest presence is achieved, but **189 legacy JSON files remain** alongside canonical manifests—likely historical per-case exports. They inflate `list`/`coverage` totals without changing adequacy structural grades. Consolidation would align CLI counts with manifest-only semantics (602 cases).

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Manifest scan | `skills/*/evals/evals.json` | canonical repo path |
| Legacy file count | `skills/*/evals/*.json` (excluding `evals.json`) | canonical repo path |
| CLI totals | `wagents eval list/adequacy --format json` | tool output |
| Regression test | `tests/test_eval_cli.py` | canonical repo path |