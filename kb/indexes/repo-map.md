---
title: Repository Map
tags:
  - kb
  - index
  - repo-map
aliases:
  - Repo map
kind: index
status: active
updated: 2026-05-01
source_count: 20
---

# Repository Map

| Path | Purpose | KB page |
|------|---------|---------|
| `AGENTS.md` | Repository standards, asset formats, workflows, platform policy. | [[agent-asset-model]], [[openspec-workflow]] |
| `README.md` | Generated/public overview, supported agents, catalog summary, user commands. | [[repository-overview]], [[developer-commands]] |
| `pyproject.toml` | Python package and tool configuration. | [[developer-commands]] |
| `Makefile` | Developer command aliases. | [[developer-commands]] |
| `skills/` | Skill source tree, eval manifests, risk/eval coverage surface. | [[skill-authoring-and-validation]], [[agent-asset-model]], [[skill-catalog-risk-and-eval-coverage]] |
| `agents/` | Agent prompt definitions and publication drift surface. | [[agent-asset-model]], [[agent-frontmatter-dialects]], [[agent-publication-and-drift-coverage]] |
| `hooks/` | Runtime hook implementation for research and control-plane policies. | [[hooks-evals-control-plane]], [[validation-and-test-coverage]] |
| `wagents/` | CLI and automation implementation. | [[repository-overview]], [[developer-commands]], [[wagents-cli-and-automation]], [[hooks-evals-control-plane]], [[skill-catalog-risk-and-eval-coverage]] |
| `config/` | Canonical registries, schemas, sync and plugin policy. | [[harness-and-platform-sync]], [[canonical-generated-surfaces]], [[sync-transaction-safety]], [[plugin-and-mcp-ownership]] |
| `instructions/` | Shared and platform-specific instruction bridges. | [[harness-and-platform-sync]], [[opencode-runtime-policy]], [[canonical-generated-surfaces]] |
| `openspec/` | Change/spec workflow and active change/archive-readiness state. | [[openspec-workflow]], [[openspec-change-archive-status]] |
| `planning/`, `agents-overhaul-planning/` | Planning corpus, sync inventory, drift ledgers, harness fixture support, and execution posture. | [[planning-corpus-and-drift-ledgers]], [[sync-transaction-safety]], [[harness-fixture-gaps]] |
| `docs/` | Astro/Starlight docs source, generated site data, and freshness gaps. | [[repository-overview]], [[docs-generation-and-site]], [[known-risks-and-open-gaps]] |
| `tests/` | Pytest validation suite. | [[developer-commands]], [[validation-and-test-coverage]], [[harness-fixture-gaps]], [[hooks-evals-control-plane]], [[skill-catalog-risk-and-eval-coverage]] |
| `mcp/` | Local MCP working area and potentially sensitive ignored paths. | [[mcp-configuration-and-safety]], [[plugin-and-mcp-ownership]], [[known-risks-and-open-gaps]] |
| `kb/` | This Nerdbot Obsidian-native operating KB. | [[nerdbot]] |
| External upstream docs | Context-only source notes for agent skills, harness docs, tooling docs, and Obsidian/Markdown docs. | [[external-primary-source-map]] |

## Evidence

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| Primary source-of-truth files include `AGENTS.md`, `instructions/global.md`, `skills/`, `agents/`, `mcp.json`, `config/`, `agent-bundle.json`, and `openspec/`. | `kb/raw/sources/openspec-config.md` | raw source note | Derived from `openspec/config.yaml`. |
| Major directory purposes were confirmed by local inventory and canonical files. | `kb/raw/sources/code-surface-inventory.md`; `kb/raw/sources/agents-md.md`; `kb/raw/sources/readme.md` | raw source notes | Consolidated map. |
| New source notes cover `wagents/`, `config/`, `docs/`, `tests/`, `mcp/`, `instructions/`, and external docs context. | `kb/raw/sources/wagents-internals.md`; `kb/raw/sources/config-registries-and-sync.md`; `kb/raw/sources/docs-site-architecture.md`; `kb/raw/sources/tests-and-validation.md`; `kb/raw/sources/mcp-surfaces.md`; `kb/raw/sources/instructions-hierarchy.md`; `kb/raw/sources/external-agent-skill-docs.md`; `kb/raw/sources/external-harness-docs.md`; `kb/raw/sources/external-tooling-docs.md`; `kb/raw/sources/external-obsidian-markdown-docs.md` | raw source notes | Enrichment map. |
| Planning manifests add sync inventory, drift, and fixture-support ledgers. | `kb/raw/sources/planning-corpus-drift-source.md` | raw source note | Planning corpus map. |
| Autoresearch source notes add hooks/evals, OpenSpec archive status, agent publication drift, skill risk/eval coverage, and docs freshness. | `kb/raw/sources/hooks-evals-control-source.md`; `kb/raw/sources/openspec-change-archive-source.md`; `kb/raw/sources/agent-publication-drift-coverage.md`; `kb/raw/sources/skill-catalog-risk-eval-coverage.md`; `kb/raw/sources/docs-artifact-freshness.md` | raw source notes | Additional KB map. |
