---
title: Glossary
tags:
  - kb
  - index
  - glossary
aliases:
  - Repository glossary
kind: index
status: active
updated: 2026-05-01
source_count: 25
---

# Glossary

| Term | Meaning | Evidence |
|------|---------|----------|
| Agent Skill | A portable agent capability stored as `skills/<name>/SKILL.md` with YAML frontmatter and Markdown body. | `kb/raw/sources/agents-md.md` |
| Agent definition | A subagent prompt file stored as `agents/<name>.md`. | `kb/raw/sources/agents-md.md`; `kb/raw/sources/code-surface-inventory.md` |
| Bundle manifest | `agent-bundle.json`, the cross-agent source map for components and adapters. | `kb/raw/sources/agent-bundle-and-sync.md` |
| Canonical material | Repo-local material treated as authoritative for the KB. | `kb/raw/sources/nerdbot-skill-contract.md`; `kb/raw/sources/openspec-config.md` |
| Generated surface | Output maintained from canonical sources, such as README/docs generated pages or projected harness config. | `kb/raw/sources/openspec-config.md`; `kb/raw/sources/agent-bundle-and-sync.md` |
| Harness | A downstream AI tool/runtime surface such as Claude Code, Codex, Gemini CLI, Copilot, Cursor, Crush, Antigravity, or OpenCode. | `kb/raw/sources/readme.md`; `kb/raw/sources/agent-bundle-and-sync.md` |
| MCP | Model Context Protocol configuration/server surface; first-party repo MCP servers follow repo conventions when authored. | `kb/raw/sources/agents-md.md` |
| OpenSpec | The repo change/spec workflow for non-trivial changes to public asset formats, downstream tooling, generated docs, sync behavior, validation, or coordinated surfaces. | `kb/raw/sources/openspec-config.md`; `kb/raw/sources/agents-md.md` |
| Nerdbot | The layered Obsidian-native KB workflow used to create and maintain this KB. | `kb/raw/sources/nerdbot-skill-contract.md` |
| raw | KB evidence layer for sources, captures, extracts, and assets. | `kb/raw/sources/nerdbot-skill-contract.md` |
| wiki | KB synthesis layer for human/agent operating knowledge. | `kb/raw/sources/nerdbot-skill-contract.md` |
| activity log | Append-only KB operation history at `activity/log.md`. | `kb/raw/sources/nerdbot-skill-contract.md` |
| Canonical surface | Repo-owned source path that should be edited instead of a generated projection. | `kb/raw/sources/config-registries-and-sync.md`; `kb/raw/sources/instructions-hierarchy.md` |
| Generated surface | Output projected from canonical sources, including README/docs pages and some harness files. | `kb/raw/sources/config-registries-and-sync.md`; `kb/raw/sources/docs-site-architecture.md` |
| Merged surface | A target config assembled from repo defaults plus live user-owned settings. | `kb/raw/sources/config-registries-and-sync.md` |
| Source plugin owner | The native plugin or repo registry that owns a harness integration so duplicate MCP projections are suppressed. | `kb/raw/sources/config-registries-and-sync.md`; `kb/raw/sources/opencode-policy-and-runtime-plugins.md`; `kb/raw/sources/mcp-surfaces.md` |
| `wagents` | The repo-local Typer CLI for validation, scaffolding, docs, packaging, install/sync, OpenSpec, hooks, and eval workflows. | `kb/raw/sources/wagents-internals.md`; `kb/raw/sources/pyproject-and-makefile.md` |
| Asset validation | Minimal structure checks for skills and agents, distinct from packaging portability checks. | `kb/raw/sources/asset-validation-coverage.md`; `kb/raw/sources/tests-and-validation.md` |
| Package dry-run | A portability check run as `uv run wagents package <name> --dry-run` or `uv run wagents package --all --dry-run`. | `kb/raw/sources/wagents-internals.md`; `kb/raw/sources/pyproject-and-makefile.md` |
| OpenCode model-neutral policy | Repo-managed OpenCode config and agent frontmatter avoid model selectors, small-model selectors, and step caps. | `kb/raw/sources/opencode-policy-and-runtime-plugins.md`; `kb/raw/sources/instructions-hierarchy.md` |
| Chrome DevTools one-owner rule | Each harness should have one Chrome DevTools owner, suppressing duplicate standalone MCP projection when a native plugin/extension owns it. | `kb/raw/sources/mcp-surfaces.md`; `kb/raw/sources/config-registries-and-sync.md` |
| External source note | A raw pointer summary for upstream docs used as context, not as repo authority. | `kb/raw/sources/external-agent-skill-docs.md`; `kb/raw/sources/external-harness-docs.md`; `kb/raw/sources/external-tooling-docs.md`; `kb/raw/sources/external-obsidian-markdown-docs.md` |
| Harness fixture gap | A validation/support-tier area where fixtures or tests do not yet prove all projected harness behavior. | `kb/raw/sources/tests-and-validation.md`; `kb/raw/sources/config-registries-and-sync.md` |
| Drift ledger | Planning manifest that records expected mode, current state, drift risk, next action, and validation command for managed sync paths. | `kb/raw/sources/planning-corpus-drift-source.md` |
| Fixture support manifest | Planning manifest that records fixture classes, validation commands, rollback status, and promotion blockers before harness support claims are raised. | `kb/raw/sources/planning-corpus-drift-source.md` |
| Hook registry | Portable config surface that maps hook IDs, events, commands, timeouts, harness support, and degraded behavior. | `kb/raw/sources/hooks-evals-control-source.md` |
| Eval manifest | Skill-local JSON contract used by `wagents eval` commands to validate and report behavioral coverage. | `kb/raw/sources/hooks-evals-control-source.md`; `kb/raw/sources/skill-catalog-risk-eval-coverage.md` |
| OpenSpec archive readiness | State where completed change tasks also have validation/status evidence and archive checklist requirements satisfied. | `kb/raw/sources/openspec-change-archive-source.md` |
| Task-complete vs archive-ready | Distinction between checked task boxes and actual OpenSpec archive eligibility. | `kb/raw/sources/openspec-change-archive-source.md` |
| Agent publication path | Route by which an agent definition appears through bundle metadata, plugin manifests, generated docs, README, or platform-specific agent corpora. | `kb/raw/sources/agent-publication-drift-coverage.md` |
| Published agent corpus | The effective set of agent definitions exposed by generated docs and platform adapters, not just files under `agents/`. | `kb/raw/sources/agent-publication-drift-coverage.md` |
| Risk tier | KB shorthand for how much harm a skill can cause if triggered or implemented incorrectly. | `kb/raw/sources/skill-catalog-risk-eval-coverage.md` |
| Eval coverage tier | KB shorthand for how deeply a skill's evals cover invocation, refusal, approval, no-mutation, and boundary behavior. | `kb/raw/sources/skill-catalog-risk-eval-coverage.md` |
| Docs artifact registry | Config registry for selected generated docs artifacts and their validation commands. | `kb/raw/sources/docs-artifact-freshness.md`; `kb/raw/sources/docs-site-architecture.md` |
| Docs freshness check | Non-mutating or low-risk check that proves generated docs outputs match source inputs. | `kb/raw/sources/docs-artifact-freshness.md` |
