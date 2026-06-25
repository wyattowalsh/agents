---
title: Harness Policy Templates Capture W12
tags:
  - kb
  - raw
  - grok
  - codex
aliases:
  - Harness policy templates 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave12-gap-sweep-2026-06-25
---

# Harness Policy Templates Capture W12

Metadata-only capture from repo-managed harness policy templates on 2026-06-25. No credential values, no live home config bodies.

## `config/grok-config.toml` (repo template)

| Section | Notable keys |
|---------|--------------|
| `[models]` | `default = grok-composer-2.5-fast`; `web_search = grok-4.20-multi-agent` |
| `[ui]` | `permission_mode = always-approve`; fork secondary model |
| `[features]` | `lsp_tools`, `codebase_indexing`; telemetry/feedback disabled |
| `[subagents]` | enabled; explore/plan toggles; depth cap in repo policy |
| `[plugins].paths` | Repo plugin path placeholders (resolved on home sync) |

Sync: `scripts/sync_agent_stack.py --apply --platforms grok` → `~/.grok/config.toml`; project MCP in `.grok/config.toml`.

## `config/codex-config.toml` (repo template)

| Key | Value |
|-----|-------|
| `model` | `gpt-5.5` |
| `model_reasoning_effort` | `xhigh` |
| `web_search` | `live` |
| `sandbox_mode` | `danger-full-access` |
| `[features]` | hooks, plugins, multi_agent, shell_tool, tool_search, … |
| MCP | Projected from `config/mcp-registry.json` via sync (names only in KB) |

Schema: `#:schema https://developers.openai.com/codex/config-schema.json`

## Distinct surfaces

| Harness | Repo SSOT | Home/live target |
|---------|-----------|------------------|
| Grok | `config/grok-config.toml` | `~/.grok/config.toml` |
| Codex | `config/codex-config.toml` | `~/.codex/config.toml` |
| OpenCode | `opencode.json` | `~/.config/opencode/opencode.json` |

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Grok template keys | `config/grok-config.toml` | canonical repo |
| Codex template keys | `config/codex-config.toml` | canonical repo |
| Prior adapter context | `kb/raw/captures/harness-config-templates-capture-w08.md` | raw capture |