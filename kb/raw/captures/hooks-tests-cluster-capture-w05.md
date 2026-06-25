---
title: Hooks Tests Cluster Capture W05
tags:
  - kb
  - raw
  - hooks
  - tests
aliases:
  - Hooks eval tests cluster 2026-06-25 wave05
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave05-hooks-tests-2026-06-25
---

# Hooks Tests Cluster Capture W05

Read-only pytest cluster inventory for hooks and eval control-plane tests on 2026-06-25 (Wave 05).

## Cluster scope

Primary files requested: `tests/test_hooks*.py`, `tests/test_eval*.py`. Adjacent hook-policy tests included for completeness.

## Test counts by file

| Test file | `def test_` count | Primary contract |
|-----------|------------------|------------------|
| `tests/test_hooks_cli.py` | 31 | `wagents hooks list/validate`, `extract_hooks`, shorthand hooks, `KNOWN_HOOK_EVENTS` (21), skill-creator `verify.py` stop/post-tool paths, `wagents validate` hook event checks |
| `tests/test_wagents_hook.py` | 33 | `hooks/wagents-hook.py` policy behavior: Codex permission shapes, Cursor native permission JSON, research readonly/shell guards, truth gates, evidence ledger, shell-write bypass hardening |
| `tests/test_eval_cli.py` | 22 | `wagents eval list/validate/coverage`; legacy JSON vs `evals.json` manifest; real-repo skill-creator single-manifest regression |
| `tests/test_eval_adequacy.py` | 10 | `wagents/eval_adequacy.py` E3/E4 detection; RV-007 risk inference (NOT-for exclusions, field-doc bullets); CLI `--strict` |
| `tests/test_hook_scan.py` | 9 | `skills/harness-master/scripts/hook_scan.py` output contract; registry/frontmatter collection; `hook-surface-registry.json` load |
| `tests/test_hook_events_sync.py` | 1 | `KNOWN_HOOK_EVENTS` parity between `wagents/parsing.py` and asset toolkit |
| `tests/test_plannotator_exit_plan_hook.py` | 2 | Grok Plannotator exit-plan hook render (adjacent harness hook) |

## Collect-only summary

```bash
uv run pytest tests/test_hooks_cli.py tests/test_eval_cli.py tests/test_eval_adequacy.py \
  tests/test_wagents_hook.py tests/test_hook_scan.py tests/test_hook_events_sync.py --collect-only -q
→ 106 tests collected
```

Extended cluster including `test_plannotator_exit_plan_hook.py`: **108** tests.

## Class / concern map (`test_hooks_cli.py`)

| Class | Concern |
|-------|---------|
| `TestExtractHooks` | Parse nested and shorthand hook dict shapes |
| `TestHooksList` | Sources: settings.json, skill frontmatter, agent frontmatter; JSON/JSONL formats |
| `TestHooksValidate` | Unknown events, handler types, empty commands; JSONL error records |
| `TestKnownEvents` | 21 known events including SessionStart, Pre/PostToolUse, Stop |
| `TestSkillCreatorVerify` | Stop guard recursion skip; post-tool SKILL.md triggers validate_hooks; dirty eval triggers validate_evals |
| `TestValidateIncludesHooks` | Repo-wide `wagents validate` catches bad hook events in settings and skills |

## Class / concern map (`test_eval_cli.py`)

| Class | Concern |
|-------|---------|
| `TestEvalList` | Manifest case counting; real-repo skill-creator ≥27 expected case ids |
| `TestEvalValidate` | Legacy required fields (`skills`, `query`, `expected_behavior`); manifest `skill_name`, `prompt`, `expected_output` |
| `TestEvalCoverage` | Per-skill `has_evals` / `eval_count`; JSONL skill records |

## Adequacy tests (`test_eval_adequacy.py`)

Covers R0–R4 tier inference, E3 explicit/implicit/negative/refusal detection, E4 boundary signals for email-like R4 skills, strict CLI exit codes, and cross-skill reference false-positive guards.

## Interpretation

Hooks and evals have **dedicated, non-overlapping** pytest clusters: CLI/schema contracts (`test_hooks_cli`, `test_eval_cli`), runtime policy behavior (`test_wagents_hook`), discovery scan (`test_hook_scan`), and structural adequacy (`test_eval_adequacy`). Real-repo smoke tests (`test_hooks_validate_real_repo`, `test_real_repo` eval paths) anchor static KB claims to executable gates.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Test inventory | `tests/test_hooks_cli.py`; `tests/test_eval_cli.py`; `tests/test_eval_adequacy.py`; `tests/test_wagents_hook.py`; `tests/test_hook_scan.py`; `tests/test_hook_events_sync.py` | canonical repo path |
| Collect count | `uv run pytest --collect-only` | tool output |