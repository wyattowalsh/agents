---
title: Instruction Overlay Matrix Capture W19
tags:
  - kb
  - raw
  - harness
aliases:
  - Instruction overlay matrix 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave19-pass3-2026-06-25
---

# Instruction Overlay Matrix Capture W19

Harness → instruction bridge matrix from `AGENTS.md` §6 and live repo paths (2026-06-25).

| Harness | Home entry | Bridge / generated source |
|---------|------------|---------------------------|
| Claude Code | `CLAUDE.md` → `@AGENTS.md` | `instructions/claude-code-global.md` |
| Codex | `AGENTS.md` | `instructions/codex-global.md` → `~/.codex/` |
| OpenCode | `AGENTS.md` | `instructions/opencode-global.md` |
| Grok Build | `AGENTS.md` | `instructions/grok-global.md` + `config/grok-config.toml` |
| Gemini CLI | `GEMINI.md` | `instructions/gemini-cli-global.md` |
| Antigravity | `GEMINI.md` | Same Gemini bridge |
| Crush | `AGENTS.md` | Shared global only |
| Cursor | `AGENTS.md` | `.cursor/rules/*.mdc` (separate schema) |
| GitHub Copilot | Generated `.github/copilot-instructions.md` | `instructions/copilot-global.md` |
| Cherry Studio | MCP registry via MCPHub | No dedicated instruction bridge |

## Sync owner

`scripts/sync_agent_stack.py` materializes generated mirrors and home projections; registries in `config/sync-manifest.json` (90 managed records per wave 17 capture).

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Supported-agent table | `AGENTS.md` §6 | canonical repo |
| Overlay files | `instructions/*-global.md` | canonical repo |