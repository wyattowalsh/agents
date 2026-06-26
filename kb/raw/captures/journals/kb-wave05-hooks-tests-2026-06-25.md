---
title: "Research journal — KB wave 05"
tags:
  - kb
  - raw
  - journal
  - provenance
aliases:
  - "KB wave 05 journal"
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave05-hooks-tests-2026-06-25
original_location: "~/.grok/research/kb-wave05-hooks-tests-2026-06-25.md"
---

# Research journal — KB wave 05

- **Goal:** `goals/kb-research-ingest/goal.md`
- **Wave:** 05 | Theme: hooks runtime test clusters and eval files
- **Captured:** 2026-06-25
- **Commit message:** `feat(kb): wave 05 — hooks runtime test clusters and eval files`

## G0 brief

Read-only inventory of `hooks/` (11 files, 16 `wagents-hook.py` policies), hook/eval pytest cluster (106 core / 108 extended tests), and `skills/*/evals/` layout (56/56 manifests, 602 manifest cases + 189 legacy JSON → CLI count 791).

## Ownership map

| Role | Artifact | Path |
|------|----------|------|
| worker | `hooks-runtime-inventory-capture-w05` | `kb/raw/captures/hooks-runtime-inventory-capture-w05.md` |
| worker | `hooks-tests-cluster-capture-w05` | `kb/raw/captures/hooks-tests-cluster-capture-w05.md` |
| worker | `skill-eval-files-capture-w05` | `kb/raw/captures/skill-eval-files-capture-w05.md` |

## Ingest queue

- `raw`: added 3 captures (`hooks-runtime-inventory-capture-w05`, `hooks-tests-cluster-capture-w05`, `skill-eval-files-capture-w05`).

## Capture evidence (excerpts)

### `hooks-runtime-inventory-capture-w05`

# Hooks Runtime Inventory Capture W05

Read-only inventory of `hooks/`, `config/hook-registry.json`, and `wagents hooks` CLI on 2026-06-25 (Wave 05).

## `hooks/` directory

| File | Role |
|------|------|
| `wagents-hook.py` | Unified policy dispatcher for Codex/Cursor/research harness hooks (16 `POLICIES`) |
| `session-start.sh` | Registry session-start handler (Copilot) |
| `log-prompt.sh` | Prompt audit log |
| `guard-destructive.sh` | Destructive shell guard |
| `protect-files.sh` | Protected path / secret guard |
| `auto-format.sh` | Post-edit formatter |
| `lint-check.sh` | Post-edit lint context |
| `verify-before-stop.sh` | Stop verification helper |
| `task-completed-gate.sh` | Task completion gate |
| `teammate-idle-gate.sh` | Teammate idle gate |
| `notify.sh` | Notification helper |

## Portable registry (`config/hook-registry.json`)

| Metric | Value |
|--------|-------|
| Registry hook entries | 22 |
| Primary harness target | `github-copilot` for shell-based registry hooks |
| Codex/Cursor policies | Routed through `wagents-hook.py` with `{repo_root}` / `{harness}` placeholders |

## `wagents-hook.py` policies (16)

Codex: `codex-session-start-context`, `codex-destructive-shell-guard`, `codex-protected-file-guard`, `codex-permission-request-guard`, `codex-post-tool-verify-context`, `codex-stop-truth-gate`.

Cursor (reuses Codex policy implementations): `cursor-session-start-context`, `cursor-destructive-shell-guard`, `cursor-protected-file-guard`, `cursor-post-tool-verify-context`, `cursor-stop-truth-gate`.

### `hooks-tests-cluster-capture-w05`

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

### `skill-eval-files-capture-w05`

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


## Key findings

Derived from command-backed captures above; canonical repo files remain authoritative.

## Metrics

**net-new raw sources: 3**; wiki pages enriched: 3; lint: pass (exit 0).

## Gate status

- G1 research: complete (read-only repo paths / external pointers)
- G2 ingest: captures written under `kb/raw/`
- G3 enrich: wiki/index updates per wave manifest
- G4 audit: `uv run python skills/nerdbot/scripts/kb_lint.py --root kb --fail-on warning` exit 0 before wave commit
