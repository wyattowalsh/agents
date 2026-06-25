---
title: Hooks Runtime Inventory Capture W05
tags:
  - kb
  - raw
  - hooks
aliases:
  - Hooks runtime capture 2026-06-25 wave05
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave05-hooks-tests-2026-06-25
---

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

Research (shared): `research-prompt-triage-context`, `research-readonly-write-guard`, `research-dangerous-shell-guard`, `research-evidence-ledger`, `research-stop-verifier`.

## CLI list snapshot (`wagents hooks list --format json`)

| Metric | Value |
|--------|-------|
| Total hooks | 40 |
| From `settings.json` | 16 |
| From `registry:*` | 22 |
| From `skill:*` | 2 (`add-badges`, `namer`) |
| `wagents-hook.py` command handlers | 31 |

### Event distribution (top)

| Event | Count |
|-------|-------|
| `PreToolUse` | 16 |
| `PostToolUse` | 9 |
| `Stop` / `stop` | 6 (mixed casing across harness dialects) |
| `UserPromptSubmit` / `beforeSubmitPrompt` | 4 |
| `SessionStart` / `sessionStart` | 4 |

## Validation

```
uv run wagents hooks validate --format json
→ {"ok": true, "error_count": 0, "message": "All hooks valid"}
```

`hooks validate` delegates to `skills/skill-creator/scripts/asset_toolkit/validate_hooks.py`. Distinct from `wagents validate` (repo-wide gate that also checks hook events in skills/agents).

## Surface registry cross-link

`config/hook-surface-registry.json` (Wave 03 capture unchanged): 9 harness rows declare authoritative/secondary hook paths. OpenCode documents plugin-internal hooks with empty `hook_surfaces`.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Policy map | `hooks/wagents-hook.py` | canonical repo path |
| Portable registry | `config/hook-registry.json` | canonical repo path |
| CLI list/validate | `wagents hooks list/validate --format json` | tool output |
| Discovery surfaces | `config/hook-surface-registry.json` | canonical repo path |