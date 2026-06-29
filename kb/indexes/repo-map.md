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
updated: 2026-06-25
source_count: 31
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
| `config/` | Canonical registries, schemas, sync and plugin policy. | [[harness-and-platform-sync]], [[canonical-generated-surfaces]], [[sync-transaction-safety]], [[plugin-and-mcp-ownership]], [[mcphub-control-plane]] |
| `config/mcp-registry.json` | MCPHub registry SSOT for local MCP control plane. | [[mcphub-control-plane]], [[mcp-configuration-and-safety]] |
| `mcp/mcphub/` | MCPHub generated settings and local control-plane projection. | [[mcphub-control-plane]] |
| `scripts/mcphub/` | MCPHub launch, tunnel, and Chrome DevTools wrapper scripts. | [[mcphub-control-plane]], [[mcp-configuration-and-safety]] |
| `scripts/sync_agent_stack.py` | Legacy harness sync monolith; dual-path with `wagents/platforms/`. | [[wagents-platform-adapters]], [[harness-and-platform-sync]] |
| `scripts/validate/` | Repo validation helpers aligned with CI/pre-commit. | [[scripts-and-validation-tooling]], [[validation-and-test-coverage]] |
| `wagents/platforms/` | Per-harness platform adapter implementations. | [[wagents-platform-adapters]], [[sync-transaction-safety]] |
| `docs/src/authoring/skills/` | Bucket A curated/custom catalog authoring SSOT (MDX). | [[curated-catalog-authoring]], [[docs-generation-and-site]] |
| `.github/workflows/` | CI and release automation (`ci.yml`, `release-skills.yml`). | [[ci-and-release-workflows]], [[validation-and-test-coverage]] |
| `instructions/` | Shared and platform-specific instruction bridges. | [[harness-and-platform-sync]], [[opencode-runtime-policy]], [[canonical-generated-surfaces]] |
| `openspec/` | Change/spec workflow and active change/archive-readiness state. | [[openspec-workflow]], [[openspec-change-archive-status]] |
| `planning/` | Active planning manifest index, sync inventory, drift ledgers, and harness fixture support. | [[planning-corpus-and-drift-ledgers]], [[sync-transaction-safety]], [[harness-fixture-gaps]] |
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
| Planning manifests add sync inventory, drift, and fixture-support ledgers. | `kb/raw/sources/planning-corpus-drift-source.md` | raw source note | Active planning manifest map. |
| Autoresearch source notes add hooks/evals, OpenSpec archive status, agent publication drift, skill risk/eval coverage, and docs freshness. | `kb/raw/sources/hooks-evals-control-source.md`; `kb/raw/sources/openspec-change-archive-source.md`; `kb/raw/sources/agent-publication-drift-coverage.md`; `kb/raw/sources/skill-catalog-risk-eval-coverage.md`; `kb/raw/sources/docs-artifact-freshness.md` | raw source notes | Additional KB map. |
| 2026-06-23 enrichment adds catalog authoring, MCPHub, platform adapters, CI, scripts validation, and OpenSpec lifecycle sources. | `kb/raw/sources/skills-catalog-authoring-lifecycle-source.md`; `kb/raw/sources/mcphub-control-plane-source.md`; `kb/raw/sources/wagents-platform-adapters-source.md`; `kb/raw/sources/ci-release-workflows-source.md`; `kb/raw/sources/scripts-validation-tooling-source.md`; `kb/raw/sources/openspec-active-lifecycle-source.md` | raw source notes | Maximal enrichment batch. |
| 2026-06-25 waves 03–10 add registry, hooks, docs authoring, MCPHub scripts, platform adapters, and external spec/harness captures. | `kb/raw/captures/mcp-registry-capture-w03.md`; `kb/raw/captures/hooks-runtime-inventory-capture-w05.md`; `kb/raw/captures/catalog-authoring-mdx-capture-w06.md`; `kb/raw/captures/mcphub-scripts-lifecycle-capture-w07.md`; `kb/raw/captures/platform-adapters-fleet-capture-w08.md`; `kb/raw/sources/agentskills-spec-capture-w09.md`; `kb/raw/sources/opencode-docs-capture-w10.md` | raw captures + external pointers | Fleet ingest evidence. |
| 2026-06-25 wave 11 deepens tooling and CI evidence. | `kb/raw/captures/pyproject-tooling-capture-w11.md`; `kb/raw/extracts/uv-llms-index-extract-w11.md`; `kb/raw/captures/ci-workflow-jobs-capture-w11.md` | raw capture + extract | Gap sweep batch. |
| 2026-06-25 passes 3–5 add instruction layer, hook registry, harness policy topics, fixture/tier registries, doctor/pytest anchors (waves 19–30). | `kb/raw/captures/instructions-layer-capture-w19.md`; `kb/raw/captures/hook-registry-capture-w20.md`; `kb/raw/captures/harness-fixture-support-capture-w23.md`; `kb/raw/captures/wagents-doctor-checks-capture-w27.md` | raw captures | 31 net-new sources; source-map `source_count: 153` at goal closure. |
