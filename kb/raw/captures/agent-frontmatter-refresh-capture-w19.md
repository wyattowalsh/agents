---
title: Agent Frontmatter Refresh Capture W19
tags:
  - kb
  - raw
  - agents
aliases:
  - Agent frontmatter refresh 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave19-pass3-2026-06-25
---

# Agent Frontmatter Refresh Capture W19

Refresh of portable vs OpenCode dialect boundaries on 2026-06-25.

## Canonical agents (9 files)

`agents/*.md` excluding `README.md`:

| Agent | Portable fields observed | OpenCode overlay |
|-------|-------------------------|------------------|
| `code-reviewer` | name, description, tools, permissionMode | mode, temperature, color, permission |
| `docs-writer` | same pattern | same |
| `orchestrator` | same pattern | same |
| `performance-profiler` | same pattern | same |
| `planner` | same pattern | same |
| `release-manager` | same pattern | same |
| `researcher` | same pattern | same |
| `security-auditor` | same pattern | same |

Plus `agents/README.md` index (not an agent definition).

## Dialect rules

- **Portable contract** (`AGENTS.md`): `name`, `description`, optional `tools`, `permissionMode`, `skills`, `mcpServers`, `memory`, `hooks` — no `model` or `steps` in repo-managed agents.
- **OpenCode overlay** (`instructions/opencode-agents-overlay.md`): `mode`, `temperature`, `color`, `permission` — loaded only by OpenCode harness.
- **Cursor projection** (`config/cursor-agents.json`): eight named subagents with `readonly` + `model: inherit`.

## Drift note

`agent-bundle.json` still maps `components.agents` to `./agents/` while historical docs mentioned reserved `agents/` paths; live count is **9** definition files.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Nine agent paths | `ls agents/*.md` | tool output |
| Overlay keys | `instructions/opencode-agents-overlay.md` | canonical repo |
| Prior inventory | `kb/raw/captures/agent-definitions-inventory-capture-w16.md` | raw capture |