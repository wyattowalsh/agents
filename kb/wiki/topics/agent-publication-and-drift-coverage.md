---
title: Agent Publication And Drift Coverage
tags:
  - kb
  - agents
  - drift
aliases:
  - Agent publication drift
  - Published agent corpus
kind: concept
status: active
updated: 2026-06-25
source_count: 3
---

# Agent Publication And Drift Coverage

## Scope

This page maps how agent definitions are published or projected. It does not resolve the drift or migrate frontmatter dialects.

## Summary

**Nine** canonical portable agents live under `agents/*.md` (2026-06-25 count). Publication spans bundle metadata (`agent-bundle.json` lists `./agents/`), plugin manifests, composed docs pages (`docs/src/content/docs/agents/*.mdx`, 8/8 composed), and platform projections including **14** files under `platforms/copilot/agents/`.

**Drift surfaces (2026-06-24):**
- Codex plugin `agents` component restored in `.codex-plugin/plugin.json`.
- Copilot corpus under `platforms/copilot/agents/` now includes all canonical eight by name plus five Copilot-only specialists (`platforms/copilot/agents/README.md`).
- Cursor adds `readonly`/`model` overlays from `config/cursor-agents.json`.
- Frontmatter dialects differ: portable minimal vs Copilot rich (`disallowedTools`, concrete `model`, `maxTurns`).

Treat coordinated reconciliation of bundle, tests, docs compose, and platform corpora as a separate fix batch after KB documentation.

## Evidence

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| Publication path inventory and drift map. | `kb/raw/sources/agent-publication-drift-coverage.md` | raw source note | Primary |
| Eight canonical agents + compose coverage. | `kb/raw/sources/agent-definitions-inventory.md` | raw source note | Counts |
| Platform adapter projection details. | `kb/raw/sources/wagents-platform-adapters-source.md` | raw source note | Copilot/Cursor/Codex gaps |
| 2026-06-25 agent corpus counts (9 canonical, 14 Copilot). | `kb/raw/captures/agent-pub-drift-capture-w01.md` | raw capture | Repo read + prior sources. |

## Related

- [[agent-frontmatter-dialects]]
- [[agent-asset-model]]
- [[canonical-generated-surfaces]]
- [[known-risks-and-open-gaps]]
