---
title: Copilot Harness Policy
tags:
  - kb
  - copilot
  - harness
aliases:
  - Copilot harness policy summary
kind: concept
status: active
updated: 2026-06-25
source_count: 3
---

# Copilot Harness Policy

## Summary

GitHub Copilot instructions are generated from `instructions/copilot-global.md` into `.github/copilot-instructions.md` and scoped `.github/instructions/*.instructions.md`. Fleet orchestration defaults to **gpt-5.4** with high reasoning and `/fleet`-optimized plans. Six shell-backed hooks are Copilot-exclusive in `config/hook-registry.json`.

## Policy themes

- `/orchestrator` tier maximization; no artificial subagent caps by default.
- Skills inventory must follow Skills CLI discovery — do not infer installs from instruction files.
- Scoped rules generated from `.claude/rules/` on repo sync.

## Related

- [[harness-and-platform-sync]]
- [[hooks-evals-control-plane]]
- [[canonical-generated-surfaces]]

## Provenance

| Claim | Source | Notes |
|-------|--------|-------|
| Fleet defaults | `kb/raw/captures/copilot-harness-policy-capture-w21.md` | Wave 21 |
| Overlay SSOT | `instructions/copilot-global.md` | Canonical repo |
| External docs | `kb/raw/sources/copilot-harness-docs-capture-w10.md` | Context only |