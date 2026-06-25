---
title: Hook Registry Capture W20
tags:
  - kb
  - raw
  - hooks
aliases:
  - Hook registry 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave20-pass3-2026-06-25
---

# Hook Registry Capture W20

Read-only snapshot of `config/hook-registry.json` on 2026-06-25.

## Summary

- **version**: 1
- **hooks**: **22** logical hook records

## Harness distribution

| Harness family | Hook IDs (count) |
|----------------|------------------|
| github-copilot | session-start, prompt-log, destructive-shell-guard, protected-file-guard, post-edit-format, post-edit-lint (6) |
| codex | codex-session-start-context, codex-destructive-shell-guard, codex-protected-file-guard, codex-permission-request-guard, codex-post-tool-verify-context, codex-stop-truth-gate (6) |
| cursor | cursor-session-start-context, cursor-destructive-shell-guard, cursor-protected-file-guard, cursor-post-tool-verify-context, cursor-stop-truth-gate (5) |
| research skill | research-prompt-triage-context, research-readonly-write-guard, research-dangerous-shell-guard, research-evidence-ledger, research-stop-verifier (5) |

## Implementation notes

- Codex/Cursor hooks route through `hooks/wagents-hook.py` with `{repo_root}` and `{harness}` placeholders.
- Copilot hooks use shell scripts under `hooks/` (format, lint, guards).
- Complements `config/hook-surface-registry.json` tier projection (wave 03 capture).

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| 22 hook IDs | `config/hook-registry.json` | canonical repo |
| Prior runtime inventory | `kb/raw/captures/hooks-runtime-inventory-capture-w05.md` | raw capture |