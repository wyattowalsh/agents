---
title: Copilot Harness Policy Capture W21
tags:
  - kb
  - raw
  - copilot
aliases:
  - Copilot policy 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave21-pass3-2026-06-25
---

# Copilot Harness Policy Capture W21

GitHub Copilot harness policy from repo surfaces on 2026-06-25.

## Instruction bridge

| Surface | Role |
|---------|------|
| `instructions/copilot-global.md` | SSOT for Copilot-specific fleet/model policy |
| `.github/copilot-instructions.md` | Generated home instructions |
| `.github/instructions/*.instructions.md` | Generated scoped rules from `.claude/rules/` |
| `AGENTS.md` | Shared asset standards (secondary) |

## Fleet policy (repo-managed)

- Plans must be `/fleet`-optimized per `/orchestrator`.
- Default model profile: **gpt-5.4**, high reasoning, `continueOnAutoMode=false`.
- No artificial subagent concurrency/depth caps unless user requests.

## Hooks (6 shell-backed)

Copilot-only hooks in `config/hook-registry.json`: session-start, prompt-log, destructive-shell-guard, protected-file-guard, post-edit-format, post-edit-lint.

## Skills inventory caveat

Copilot stays in harness sync but installed-skill inventory should report only Skills CLI discoveries — do not fabricate rows from instruction files.

## External context

`kb/raw/sources/copilot-harness-docs-capture-w10.md`.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Fleet defaults | `instructions/copilot-global.md` | canonical repo |
| Hook list | `config/hook-registry.json` | canonical repo |