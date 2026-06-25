---
title: Cursor Harness Policy Capture W21
tags:
  - kb
  - raw
  - cursor
aliases:
  - Cursor policy 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave21-pass3-2026-06-25
---

# Cursor Harness Policy Capture W21

Cursor harness policy from repo-managed surfaces on 2026-06-25.

## Instruction bridge

- Home: `AGENTS.md` → `@instructions/global.md` (no `instructions/cursor-global.md`).
- Scoped rules: `.cursor/rules/*.mdc` — separate schema from Claude `.claude/rules/`.
- Home sync copies `.cursor/rules/` to `~/.cursor/rules/` on stack sync.

## Subagent registry

`config/cursor-agents.json` — **8** named agents mirroring repo `agents/` names with `readonly` flags and `model: inherit`:

code-reviewer, docs-writer, orchestrator, performance-profiler, planner, release-manager, researcher, security-auditor.

## Hooks (5)

From `config/hook-registry.json`: session-start-context, destructive-shell-guard, protected-file-guard, post-tool-verify-context, stop-truth-gate — all via `wagents-hook.py`.

## Fixture tier

`planning/manifests/harness-fixture-support.json`: multiple Cursor surfaces (`cursor-acp`, `cursor-bugbot`, `cursor-cli`, `cursor-editor`, `cursor-cloud-agent`, `cursor-cloud-subagent`) with mixed fixture-executable vs plan-only status.

## External context

`kb/raw/sources/cursor-docs-capture-w10.md` — upstream docs pointer only.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Agent registry | `config/cursor-agents.json` | canonical repo |
| Hook IDs | `config/hook-registry.json` | canonical repo |