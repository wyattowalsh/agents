---
title: Codex Harness Policy Capture W15
tags:
  - kb
  - raw
  - codex
aliases:
  - Codex policy 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave15-pass2-2026-06-25
---

# Codex Harness Policy Capture W15

Metadata-only read of `config/codex-config.toml` and `instructions/codex-global.md` on 2026-06-25.

## Core runtime

| Key | Value |
|-----|-------|
| `model` | `gpt-5.5` |
| `model_reasoning_effort` | `xhigh` |
| `web_search` | `live` |
| `sandbox_mode` | `danger-full-access` |
| `approval_policy` | `never` |
| Schema | `#:schema https://developers.openai.com/codex/config-schema.json` |

## Features (selected)

hooks, plugins, multi_agent, shell_tool, tool_search, memories, image_generation, workspace_dependencies enabled; `multi_agent_v2 = false`.

## Web search

Top-level `web_search = "live"`; tune via `[tools.web_search]` (not deprecated `features.web_search*` toggles per repo policy).

## Skills discovery

Repo policy: Codex disables automatic startup skill-list injection; recovery via `wagents skills search|context|read|doctor`.

## Sync surfaces

| Surface | Role |
|---------|------|
| `config/codex-config.toml` | Repo SSOT → `~/.codex/config.toml` |
| `.codex-plugin/plugin.json` | Plugin adapter |
| `wagents/platforms/codex.py` | Thin delegator (~46 LOC) to monolith sync |

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| TOML keys | `config/codex-config.toml` | canonical repo |
| Instruction overlay | `instructions/codex-global.md` | canonical repo |
| Prior template | `kb/raw/captures/harness-policy-templates-capture-w12.md` | raw capture |