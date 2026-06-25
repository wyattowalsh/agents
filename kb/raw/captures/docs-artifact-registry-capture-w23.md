---
title: Docs Artifact Registry Capture W23
tags:
  - kb
  - raw
  - docs
aliases:
  - Docs artifact registry 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave23-pass4-2026-06-25
---

# Docs Artifact Registry Capture W23

Snapshot of `config/docs-artifact-registry.json` on 2026-06-25.

## Counts

- **source_registries**: 7 upstream registries (support-tier, harness-surface, mcp, hook, sync-manifest, agent-bundle, catalog authoring)
- **artifacts**: 14 tracked paths
- **docs_truth_rules**: 7 policy bullets

## Artifact modes

| Mode | Examples |
|------|----------|
| generated | README.md, `docs/src/generated-*.mjs`, catalog index JSON, skills/agents content trees |
| mixed | `docs/src/content/docs/mcp/` (hand + generated) |

## Validation commands (recurring)

- `uv run wagents readme --check`
- `uv run wagents docs generate --no-installed --check`
- `uv run wagents catalog index --check`

## Truth rules highlight

- Support matrices must distinguish desktop/web/CLI/editor/experimental surfaces.
- Install commands only from supported adapter records.
- MCP overview badges must match `mcp.json` server count.
- Skill catalog URLs use grouped `skills/catalog/custom|external/` paths only.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Artifact list | `config/docs-artifact-registry.json` | canonical repo |
| Prior freshness | `kb/raw/sources/docs-artifact-freshness.md` | raw source |