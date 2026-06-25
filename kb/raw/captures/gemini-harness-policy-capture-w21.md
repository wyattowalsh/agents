---
title: Gemini Harness Policy Capture W21
tags:
  - kb
  - raw
  - gemini
aliases:
  - Gemini policy 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave21-pass3-2026-06-25
---

# Gemini Harness Policy Capture W21

Gemini CLI / Antigravity bridge policy from repo surfaces on 2026-06-25.

## Entrypoints

| Surface | Path |
|---------|------|
| Gemini CLI home | `GEMINI.md` → `@./AGENTS.md` → `@instructions/global.md` |
| Antigravity | Same `GEMINI.md` bridge |
| Platform overlay | `instructions/gemini-cli-global.md` |

## Repo-managed policy themes

- **Tool efficiency**: prefer narrow grep/glob, parallel reads, scoped line limits.
- **Safety**: explain shell commands; never log secrets; non-interactive defaults.
- **Execution lifecycle**: Research → Strategy → Execution; `enter_plan_mode` for complex work.
- **Subagents**: maximize independent dispatch (`generalist`, `codebase_investigator`).

## Adapter / sync

No dedicated `config/gemini-*.toml` in repo; harness sync flows through `scripts/sync_agent_stack.py` and Skills CLI adapter (`agent-skills-cli` in `agent-bundle.json`). External pointer: `kb/raw/sources/gemini-harness-docs-capture-w13.md`.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Bridge chain | `AGENTS.md` §6 | canonical repo |
| Overlay bullets | `instructions/gemini-cli-global.md` | canonical repo |