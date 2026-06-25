---
title: Codex Harness Policy
tags:
  - kb
  - codex
  - harness
aliases:
  - Codex policy
kind: concept
status: active
updated: 2026-06-25
source_count: 3
---

# Codex Harness Policy

## Summary

Codex uses repo-managed `config/codex-config.toml` merged into `~/.codex/config.toml`. Default model is `gpt-5.5` with `xhigh` reasoning; `web_search = "live"`. The `wagents/platforms/codex.py` adapter is a thin delegator (~46 LOC) to the sync monolith — most projection logic lives in `scripts/sync_agent_stack.py` and shared platform helpers.

## Why it matters

- Codex disables automatic startup skill-list injection to protect context budget; use `wagents skills` recovery commands when skills are omitted.
- Config validates against OpenAI's published schema URL embedded in the TOML header.
- `scripts/validate_codex_config.py` exists but is not CI-gated as of 2026-06-25.

## Current shape

| Key area | Repo policy |
|----------|-------------|
| Model | `gpt-5.5`, reasoning `xhigh` |
| Web search | `live` + `[tools.web_search]` tuning |
| Sandbox | `danger-full-access` (managed profile) |
| Features | hooks, plugins, multi_agent, shell_tool, tool_search, memories |
| Plugin | `.codex-plugin/plugin.json` + `.agents/plugins/marketplace.json` |

## Constraints

- Do not rely on deprecated `features.web_search*` toggles.
- Chrome DevTools may use upstream plugin when installed; repo MCP is fallback for MCP-only harnesses.
- Parent harnesses may dispatch Grok nodes via `/grok-delegate`; Codex config sync is separate from Grok policy.

## Provenance

| Claim | Source | Notes |
|-------|--------|-------|
| TOML policy keys | `kb/raw/captures/codex-harness-policy-capture-w15.md` | Wave 15 |
| Template baseline | `kb/raw/captures/harness-policy-templates-capture-w12.md` | Wave 12 |
| Instruction overlay | `instructions/codex-global.md` | Canonical repo |

## Related

- [[harness-and-platform-sync]]
- [[wagents-platform-adapters]]
- [[canonical-generated-surfaces]]
- [[scripts-and-validation-tooling]]