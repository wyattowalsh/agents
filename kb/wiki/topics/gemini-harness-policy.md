---
title: Gemini Harness Policy
tags:
  - kb
  - gemini
  - harness
aliases:
  - Gemini policy
kind: concept
status: active
updated: 2026-06-25
source_count: 3
---

# Gemini Harness Policy

## Summary

Gemini CLI reads `GEMINI.md` → `@./AGENTS.md` → `@instructions/global.md` with a thin efficiency overlay in `instructions/gemini-cli-global.md`. Antigravity shares the same bridge. There is no repo-owned `config/gemini-*.toml`; sync flows through Skills CLI and `sync_agent_stack.py`.

## Policy themes

- Narrow tool usage: grep/glob first, parallel reads, scoped line limits.
- Explain-before-act for shell and modifying commands.
- Research → Strategy → Execution lifecycle; plan mode for complex edits.
- Independent subagent dispatch encouraged.

## Related

- [[harness-and-platform-sync]]
- [[external-primary-source-map]]
- [[antigravity-harness-policy]]

## Provenance

| Claim | Source | Notes |
|-------|--------|-------|
| Bridge chain | `kb/raw/captures/gemini-harness-policy-capture-w21.md` | Wave 21 |
| External docs | `kb/raw/sources/gemini-harness-docs-capture-w13.md` | Context only |
| Overlay | `instructions/gemini-cli-global.md` | Canonical repo |