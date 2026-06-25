---
title: Cursor Harness Policy
tags:
  - kb
  - cursor
  - harness
aliases:
  - Cursor harness policy summary
kind: concept
status: active
updated: 2026-06-25
source_count: 3
---

# Cursor Harness Policy

## Summary

Cursor uses `AGENTS.md` as the home instruction bridge plus independent `.cursor/rules/*.mdc` scoped rules (not mirrored from Claude rules). Subagent names are projected via `config/cursor-agents.json` (eight agents, `model: inherit`). Five Codex-style hooks run through `wagents-hook.py`.

## Surfaces

| Surface | Role |
|---------|------|
| `AGENTS.md` | Shared standards |
| `.cursor/rules/*.mdc` | Path-conditional Cursor rules |
| `config/cursor-agents.json` | Subagent registry |
| `config/hook-registry.json` | Cursor hook IDs |

## Fixture posture

Multiple Cursor harness IDs in `harness-fixture-support.json` (`cursor-acp`, `cursor-cli`, `cursor-editor`, cloud variants) with mixed executable vs plan-only fixtures.

## Related

- [[harness-and-platform-sync]]
- [[hooks-evals-control-plane]]
- [[harness-fixture-gaps]]
- [[wagents-platform-adapters]]

## Provenance

| Claim | Source | Notes |
|-------|--------|-------|
| Registry + hooks | `kb/raw/captures/cursor-harness-policy-capture-w21.md` | Wave 21 |
| External docs | `kb/raw/sources/cursor-docs-capture-w10.md` | Context only |