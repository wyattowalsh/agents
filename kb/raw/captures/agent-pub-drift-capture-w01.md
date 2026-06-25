---
title: Agent Publication Drift Capture W01
tags:
  - kb
  - raw
  - agents
aliases:
  - Agent pub capture 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave01-partials-2026-06-25
---

# Agent Publication Drift Capture W01

Read-only agent publication inventory on 2026-06-25.

## Corpus counts

| Surface | Count | Path |
|---------|-------|------|
| Canonical portable agents | 9 | `agents/*.md` |
| Copilot projected agents | 14 | `platforms/copilot/agents/*.md` |
| Composed docs agent pages | 8 | `docs/src/content/docs/agents/` (per prior KB; compose 8/8) |

## Drift notes

- Copilot corpus includes canonical eight by name plus Copilot-only specialists (documented in `platforms/copilot/agents/README.md`).
- Codex plugin `plugin.json` components list empty in current read — verify against `.codex-plugin/plugin.json` and bundle metadata before claiming plugin agent projection.
- Cursor overlays from `config/cursor-agents.json` add `readonly`/`model` fields beyond portable frontmatter.

## KB posture

Document projection surfaces and dialect differences; coordinated reconciliation of bundle, tests, docs compose, and platform corpora remains a separate repo fix batch.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Agent file counts | `agents/`, `platforms/copilot/agents/` | repo read |
| Publication map | `kb/raw/sources/agent-publication-drift-coverage.md` | prior KB source |