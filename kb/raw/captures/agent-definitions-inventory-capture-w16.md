---
title: Agent Definitions Inventory Capture W16
tags:
  - kb
  - raw
  - agents
aliases:
  - Agent inventory 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave16-pass2-2026-06-25
---

# Agent Definitions Inventory Capture W16

Explicit listing of `agents/` on 2026-06-25.

## Canonical agent files (8)

| File | `name` field expected |
|------|---------------------|
| `code-reviewer.md` | `code-reviewer` |
| `docs-writer.md` | `docs-writer` |
| `orchestrator.md` | `orchestrator` |
| `performance-profiler.md` | `performance-profiler` |
| `planner.md` | `planner` |
| `release-manager.md` | `release-manager` |
| `researcher.md` | `researcher` |
| `security-auditor.md` | `security-auditor` |

Plus `agents/README.md` index (not an agent definition).

## Drift note

`agent-bundle.json` may still describe `agents/` as reserved/future while eight definitions exist. Reconcile in repo docs, not KB authority.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| File list | `ls agents/` | tool capture |
| Prior drift | `kb/raw/sources/agent-definitions-inventory.md`; `kb/wiki/topics/agent-asset-model.md` | raw + wiki |