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
updated: 2026-07-29
source_count: 3
---

# Cursor Harness Policy

## Summary

Cursor uses `AGENTS.md` as the home instruction bridge plus independent `.cursor/rules/*.mdc` scoped rules (not mirrored from Claude rules). Subagent names are projected via `config/cursor-agents.json` (20 agents, `model: cursor-grok-4.5-high`). Always-on pin rule: `.cursor/rules/cursor-models.mdc` (quotes layer matrix SSOT). Home sync copies allowlisted rules to `~/.cursor/rules/` (preserve orphans) and managed-marker agents to `~/.cursor/agents/`. Model enforcement layers: soft rule (agents must not omit) + `cursor-task-model-pin-rewrite` (preToolUse Task rewrite, fail-open) + `cursor-subagent-model-allowlist` (subagentStart; omit allowed, deny explicit non-High). Operators SHOULD set user-owned `~/.cursor/cli-config.json` `exploreSubagentModel=inherit` and IDE picker to Grok 4.5 High; sync SHALL NOT write `cli-config` or live `state.vscdb`. Fleet hooks run through `wagents-hook.py`.

## Layer matrix (SSOT)

| Layer | Mechanism | Omit `model` | Wrong/fast model | Hook crash |
| --- | --- | --- | --- | --- |
| Soft rule | `.cursor/rules/cursor-models.mdc` | Agents must not omit | Agents must not pass | N/A |
| Phase A | `preToolUse` Task rewrite | Pins to High via `updated_input` | Rewrites + clears alts | **fail-open** (Task proceeds) |
| Phase B | `subagentStart` allowlist | Allow (inherit High parent) | Deny if explicit non-High | **fail-open** |
| Validate/CI | `validate_hooks` + pytest | N/A | N/A | Compensatory: projection **must** exist |

Security Enforce guards stay **fail-closed** (RV-004). Pin hooks stay **fail-open**.

## Surfaces

| Surface | Role |
|---------|------|
| `AGENTS.md` | Shared standards |
| `.cursor/rules/*.mdc` | Path-conditional Cursor rules (incl. always-on `cursor-models.mdc`) |
| `config/cursor-agents.json` | Subagent registry (20 agents, `cursor-grok-4.5-high`) |
| `config/hook-registry.json` | Cursor hook IDs (`cursor-task-model-pin-rewrite`, `cursor-subagent-model-allowlist`, …) |
| `~/.cursor/rules/` | Home allowlisted rule projection (orphans preserved) |
| `~/.cursor/agents/` | Home managed-marker agent projection |
| `~/.cursor/cli-config.json` | Local CLI (`exploreSubagentModel=inherit`; operator SHOULD; user-owned; sync SHALL NOT write) |

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
| Grok 4.5 High pin | `.cursor/rules/cursor-models.mdc`; `config/cursor-agents.json`; hook registry; hooks hub layer matrix | 2026-07-29 |
