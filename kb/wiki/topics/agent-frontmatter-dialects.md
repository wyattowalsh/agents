---
title: Agent Frontmatter Dialects
tags:
  - kb
  - agents
  - frontmatter
aliases:
  - Agent dialects
kind: concept
status: active
updated: 2026-05-01
source_count: 4
---

# Agent Frontmatter Dialects

## Scope

This page documents the current dialect split. It does not propose or execute a migration.

## Summary

`AGENTS.md` defines a cross-platform agent file contract with required `name` and `description`, plus optional fields such as `tools`, `disallowedTools`, `model`, `permissionMode`, `maxTurns`, `skills`, `mcpServers`, `memory`, and `hooks`. Current repo agent files use an OpenCode-style dialect with fields such as `mode`, `temperature`, `color`, and `permission`.

That dialect difference matters because docs rendering, sync projections, and validators may not consume the same fields. The safest operating rule is to preserve current agent files as canonical repo assets and route intentional dialect changes through OpenSpec and tests. Repo-managed agents must remain model-neutral: tests reject `model:` and `steps:` in agent frontmatter.

Publication drift adds a second layer to the dialect problem: active repo agents are published through README/docs and plugin/platform surfaces while bundle metadata still contains reserved-agent wording. Treat dialect changes and publication changes as one coordinated surface, not independent cleanup.

## Evidence

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| The documented agent table differs from current repo agent file fields. | `kb/raw/sources/agent-definitions-inventory.md`; `kb/raw/sources/asset-validation-coverage.md` | raw source notes | Existing drift documented, not fixed. |
| There are eight current agent definition files under `agents/`. | `kb/raw/sources/agent-definitions-inventory.md` | raw source note | Inventory finding. |
| Tests protect model-neutral agent files. | `kb/raw/sources/asset-validation-coverage.md`; `kb/raw/sources/opencode-policy-and-runtime-plugins.md` | raw source notes | Avoid adding `model` or `steps`. |
| Publication drift spans bundle metadata, generated docs, plugin manifests, and platform-specific agent corpora. | `kb/raw/sources/agent-publication-drift-coverage.md` | raw source note | Publication surface context. |

## Related

- [[agent-asset-model]]
- [[validation-and-test-coverage]]
- [[agent-publication-and-drift-coverage]]
- [[known-risks-and-open-gaps]]
