---
title: Agent Bundle Snapshot Capture W23
tags:
  - kb
  - raw
  - bundle
aliases:
  - Agent bundle snapshot 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave23-pass4-2026-06-25
---

# Agent Bundle Snapshot Capture W23

Read-only snapshot of `agent-bundle.json` on 2026-06-25.

## Components

| Key | Path |
|-----|------|
| skills | `./skills/` |
| agents | `./agents/` |
| mcpServers | `./mcp.json` |
| instructions | `./instructions/` |
| openspec | `./openspec/` |

## Adapters (6 families)

claude-code, codex, agent-skills-cli, wagents-cli, openspec, apm

## Skills CLI supported agents (10)

grok, antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, opencode

## Install paths

- Claude: `claude plugin install agents@agents`
- Codex: marketplace UI install
- Skills CLI: `npx skills add github:wyattowalsh/agents --all ...`
- wagents: `uv tool install wagents --from git+...`
- OpenSpec: `uv run wagents openspec init --apply`
- APM: `apm install wyattowalsh/agents`

## Drift note

Bundle maps `agents` to `./agents/`; live inventory is **9** agent `.md` files + README (wave 19 refresh). No fixed `version` field — Git commit is update source.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| JSON structure | `agent-bundle.json` | canonical repo |
| Prior pointer | `kb/raw/sources/agent-bundle-and-sync.md` | raw source |