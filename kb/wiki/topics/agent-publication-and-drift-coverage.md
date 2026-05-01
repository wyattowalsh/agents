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
updated: 2026-05-01
source_count: 1
---

# Agent Publication And Drift Coverage

## Scope

This page maps how agent definitions are published or projected. It does not resolve the drift or migrate frontmatter dialects.

## Summary

Agent publication is currently split across canonical repo agent files, bundle metadata, plugin manifests, generated README/docs surfaces, and platform-specific Copilot agent files. The most important drift is that bundle metadata still describes `agents/` as reserved while active agent files and generated public docs expose an agent catalog.

The drift matters because tests currently assert some stale wording, docs rendering emphasizes cross-platform fields more than current OpenCode-style agent fields, and platform-specific agent corpora can differ in names or permissions. Treat this as a source-of-truth and generated-surface gap until the bundle, docs generator, tests, and platform projections are reconciled together.

## Evidence

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| Agent publication spans bundle metadata, repo agents, generated docs, plugin manifests, and platform-specific agent files. | `kb/raw/sources/agent-publication-drift-coverage.md` | raw source note | Dedicated source note. |
| `agent-bundle.json` reserved wording conflicts with active agents and generated docs. | `kb/raw/sources/agent-publication-drift-coverage.md` | raw source note | Drift candidate. |
| Agent dialect and docs rendering behavior need a coordinated decision before changes. | `kb/raw/sources/agent-publication-drift-coverage.md` | raw source note | Avoids accidental migration. |

## Related

- [[agent-frontmatter-dialects]]
- [[agent-asset-model]]
- [[canonical-generated-surfaces]]
- [[known-risks-and-open-gaps]]
