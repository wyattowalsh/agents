---
title: Grok Harness Policy Capture W15
tags:
  - kb
  - raw
  - grok
aliases:
  - Grok policy 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave15-pass2-2026-06-25
---

# Grok Harness Policy Capture W15

Metadata-only read of `config/grok-config.toml` and `instructions/grok-global.md` on 2026-06-25.

## Models and UI

| Key | Value |
|-----|-------|
| `models.default` | `grok-composer-2.5-fast` |
| `models.web_search` | `grok-4.20-multi-agent` |
| `ui.permission_mode` | `always-approve` |
| `ui.yolo` | `true` |

## Features and session

| Area | Policy |
|------|--------|
| `features` | `lsp_tools`, `codebase_indexing`; telemetry/feedback off |
| `session.auto_compact_threshold_percent` | 95 |
| `tools.respect_gitignore` | false |
| `toolset.bash.timeout_secs` | 86400 |

## Subagents

Enabled with depth cap **1** (repo instruction policy). Models: explore/plan/general-purpose → `grok-composer-2.5-fast`.

## Memory

`memory.enabled = true`; session save on end; watcher on; search `max_results = 12`, `min_score = 0.25`.

## Compat layers

`compat.cursor` and `compat.claude` each enable skills, rules, agents, mcps, hooks mirroring.

## Sync surfaces

| Surface | Role |
|---------|------|
| `config/grok-config.toml` | Repo SSOT → `~/.grok/config.toml` |
| `.grok/config.toml` | Project MCP (+ optional plugins) |
| `config/grok-plannotator-hooks.json` | Plannotator hook policy |
| `wagents/platforms/grok.py` | Adapter (~602 LOC) |

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| TOML keys | `config/grok-config.toml` | canonical repo |
| Instruction overlay | `instructions/grok-global.md` | canonical repo |
| Prior template | `kb/raw/captures/harness-policy-templates-capture-w12.md` | raw capture |