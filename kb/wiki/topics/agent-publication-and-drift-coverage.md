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
status: partial
updated: 2026-06-23
source_count: 2
---

# Agent Publication And Drift Coverage

## Scope

This page maps how agent definitions are published or projected. It does not resolve the drift or migrate frontmatter dialects.

## Summary

Eight canonical portable agents live under `agents/*.md`. Publication spans bundle metadata (`agent-bundle.json` lists `./agents/`), plugin manifests, composed docs pages (`docs/src/content/docs/agents/*.mdx`, 8/8 composed, hand-maintained since 2026-06-17), and platform projections.

**Drift surfaces (2026-06-23):**
- Codex plugin paths (`.codex-plugin/plugin.json`, `.agents/plugins/marketplace.json`) are declared in harness registry/tests but missing on disk.
- Copilot corpus under `platforms/copilot/agents/` has 11 files with only partial overlap to canonical eight (renames + specialists).
- Cursor adds `readonly`/`model` overlays from `config/cursor-agents.json`.
- Frontmatter dialects differ: portable minimal vs Copilot rich (`disallowedTools`, concrete `model`, `maxTurns`).

Treat coordinated reconciliation of bundle, tests, docs compose, and platform corpora as a separate fix batch after KB documentation.

## Evidence

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| Publication path inventory and drift map. | `kb/raw/sources/agent-publication-drift-coverage.md` | raw source note | Primary |
| Eight canonical agents + compose coverage. | `kb/raw/sources/agent-definitions-inventory.md` | raw source note | Counts |
| Platform adapter projection details. | `kb/raw/sources/wagents-platform-adapters-source.md` | raw source note | Copilot/Cursor/Codex gaps |

## Related

- [[agent-frontmatter-dialects]]
- [[agent-asset-model]]
- [[canonical-generated-surfaces]]
- [[known-risks-and-open-gaps]]
