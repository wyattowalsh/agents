---
title: Grok Harness Policy
tags:
  - kb
  - grok
  - harness
aliases:
  - Grok policy
kind: concept
status: active
updated: 2026-06-25
source_count: 3
---

# Grok Harness Policy

## Summary

Grok Build is a first-class harness with repo-managed home policy in `config/grok-config.toml`, project MCP in `.grok/config.toml`, and a native `wagents/platforms/grok.py` adapter. Default model is `grok-composer-2.5-fast`; web search routes to `grok-4.20-multi-agent`. Subagent depth is hard-capped at **1** per repo instruction policy.

## Why it matters

- Grok is not a thin delegator — local adapter code owns TOML merge, MCP projection, skills mirror, and LSP feature flags.
- Compat layers mirror Claude/Cursor skills, rules, agents, MCP, and hooks into Grok discovery paths.
- Plannotator uses CLI + skills + synced hooks (`config/grok-plannotator-hooks.json`), not an npm plugin like OpenCode.

## Current shape

| Surface | Role |
|---------|------|
| `config/grok-config.toml` | Repo SSOT for models, UI, features, memory, subagents, compat |
| `instructions/grok-global.md` | Platform overlay (env vars, plannotator, sync commands) |
| `wagents/platforms/grok.py` | Native adapter implementation |
| `~/.grok/config.toml` | Live home merge target |

## Constraints

- Experimental toggles may be env-only (`config/grok-env.sh`); run `wagents grok doctor --format json` after changes.
- Restart Grok Build after config/hook changes.
- Cross-harness parents may delegate via `/grok-delegate`; Grok should not nest graphs beyond depth 1.

## Provenance

| Claim | Source | Notes |
|-------|--------|-------|
| TOML policy keys | `kb/raw/captures/grok-harness-policy-capture-w15.md` | Wave 15 |
| Template baseline | `kb/raw/captures/harness-policy-templates-capture-w12.md` | Wave 12 |
| Instruction overlay | `instructions/grok-global.md` | Canonical repo |

## Related

- [[harness-and-platform-sync]]
- [[wagents-platform-adapters]]
- [[plugin-and-mcp-ownership]]
- [[harness-fixture-gaps]]