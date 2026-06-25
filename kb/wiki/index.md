---
title: Agents Repository Operating Knowledge Base
tags:
  - kb
  - agents-repo
aliases:
  - Agents KB
  - Repository KB
kind: overview
status: active
updated: 2026-06-25
source_count: 28
---

# Agents Repository Operating Knowledge Base

## Scope

This Obsidian-native KB helps future agents understand and operate the `agents` repository. It is an operating knowledge base, not a generated documentation mirror. It favors stable source-backed synthesis, navigation, provenance, and unresolved-gap tracking.

## Canonical Material

Treat these repo files and directories as primary evidence before using generated public surfaces:

| Surface | Role |
|---------|------|
| `AGENTS.md` | Asset standards, repo workflow, supported agents, bundle/plugin conventions. |
| `instructions/global.md` and platform instruction files | Cross-platform and harness-specific operating rules. |
| `skills/` | Skill definitions and skill-specific contract material. |
| `agents/` | Agent prompt definitions. |
| `wagents/` | Repository CLI and automation implementation. |
| `config/` | Canonical registries and generated/merged surface policy. |
| `openspec/` | Change workflow specs, schemas, active changes, and OpenSpec config. |
| `Makefile`, `pyproject.toml` | Developer command and tooling configuration. |

## Current Wiki Map

| Page | Use it for |
|------|------------|
| [[repository-overview]] | Fast orientation to what the repo is and how it is organized. |
| [[agent-asset-model]] | Skills, agents, MCP, instructions, plugins, and bundle surfaces. |
| [[skill-authoring-and-validation]] | Skill format, naming, validation, packaging, and docs implications. |
| [[harness-and-platform-sync]] | How repo-owned assets reach Claude, Codex, OpenCode, Gemini, Copilot, and related harnesses. |
| [[grok-harness-policy]] | Grok Build models, memory, subagents, compat layers, and sync surfaces. |
| [[codex-harness-policy]] | Codex model/search/sandbox policy and thin adapter delegation model. |
| [[gemini-harness-policy]] | Gemini CLI / Antigravity GEMINI.md bridge and tool-efficiency overlay. |
| [[cursor-harness-policy]] | Cursor AGENTS.md bridge, .mdc rules, subagent registry, and hooks. |
| [[copilot-harness-policy]] | Copilot generated instructions, fleet model policy, and shell hooks. |
| [[antigravity-harness-policy]] | Antigravity Gemini bridge and fixture tier summary. |
| [[crush-harness-policy]] | Crush minimal instruction bridge and experimental fixture tier. |
| [[nerdbot]] | How this KB is structured and how to maintain it safely. |
| [[openspec-workflow]] | When OpenSpec is required and how wrapper commands are used. |
| [[developer-commands]] | Verified commands for validation, tests, docs, packaging, OpenSpec, and KB lint. |
| [[known-risks-and-open-gaps]] | Current confidence limits, dirty worktree state, local-only areas, and follow-up queue. |
| [[wagents-cli-and-automation]] | CLI implementation, command families, and package dry-run gotchas. |
| [[validation-and-test-coverage]] | How asset validation, packaging, docs checks, tests, and KB lint differ. |
| [[agent-frontmatter-dialects]] | Repo agent fields and cross-platform frontmatter dialect boundaries. |
| [[mcp-configuration-and-safety]] | MCP registries, local MCP areas, secret boundaries, and safe ingestion rules. |
| [[docs-generation-and-site]] | README/docs generation, Starlight site structure, and generated data surfaces. |
| [[opencode-runtime-policy]] | OpenCode model-neutral config, runtime plugins, telemetry, and Chrome DevTools policy. |
| [[opencode-harness-policy]] | OpenCode adapter scale, canonical config files, and plugin/DCP policy summary. |
| [[canonical-generated-surfaces]] | Canonical, generated, merged, and symlinked surface ownership. |
| [[sync-transaction-safety]] | Sync transaction behavior, rollback limits, and safety gaps. |
| [[plugin-and-mcp-ownership]] | Plugin and MCP ownership rules that prevent duplicate projections. |
| [[harness-fixture-gaps]] | Current fixture and support-tier validation gaps. |
| [[external-primary-source-map]] | Upstream docs fetched for context and how they relate to repo-local authority. |
| [[planning-corpus-and-drift-ledgers]] | Planning manifests, drift ledgers, and fixture support blockers for sync work. |
| [[hooks-evals-control-plane]] | Hook registry, runtime guards, projection logic, and skill eval control surfaces. |
| [[openspec-change-archive-status]] | Active OpenSpec change inventory and archive-readiness distinction. |
| [[agent-publication-and-drift-coverage]] | Agent publication paths, docs/plugin surfaces, and drift candidates. |
| [[skill-catalog-risk-and-eval-coverage]] | Risk-adjusted interpretation of skill eval coverage. |
| [[obsidian-vault-conventions]] | Obsidian-native vault conventions for this KB. |
| [[curated-catalog-authoring]] | Bucket A catalog authoring SSOT and index generation pipeline. |
| [[mcphub-control-plane]] | MCPHub registry, groups, tunnel, and client projection. |
| [[wagents-platform-adapters]] | Per-harness platform adapters and sync safety guards. |
| [[ci-and-release-workflows]] | CI seven-job matrix and release-skills workflow gates. |
| [[scripts-and-validation-tooling]] | `scripts/` validation helpers and CI/pre-commit alignment. |

## Related Indexes

- [[source-map]]
- [[coverage]]
- [[repo-map]]
- [[glossary]]
- [[log]]

## Current Confidence

Confidence is high for repository purpose, asset format, command surfaces, OpenSpec policy, Nerdbot KB structure, `wagents` command families, Bucket A catalog semantics, MCPHub registry topology, CI workflow structure, and registry/sync ownership because these are backed by local canonical files and 2026-06-23 read-only research. Confidence is partial for full harness behavior, generated docs health (compose 98.2%, stale MCP badge), rollback completeness, OpenSpec archive readiness (~32 active changes), risk-adjusted skill eval adequacy (29/56 manifests), and live CI pass status because this batch did not run the full test/CI matrix.

## Evidence

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| This repository is for portable AI agent skills, MCP configuration, and shared instructions. | `kb/raw/sources/readme.md`; `kb/raw/sources/openspec-config.md` | raw source notes | Public README and OpenSpec context agree. |
| Canonical source-of-truth surfaces include `AGENTS.md`, `instructions/global.md`, `skills/`, `agents/`, `mcp.json`, `config/`, `agent-bundle.json`, and `openspec/`. | `kb/raw/sources/openspec-config.md` | raw source note | Derived from `openspec/config.yaml`. |
| This KB follows the Nerdbot layered model. | `kb/raw/sources/nerdbot-skill-contract.md` | raw source note | Derived from Nerdbot contract and references. |
| Expanded coverage includes `wagents`, validation/tests, docs generation, MCP, OpenCode, and sync ownership. | `kb/raw/sources/wagents-internals.md`; `kb/raw/sources/tests-and-validation.md`; `kb/raw/sources/config-registries-and-sync.md`; `kb/raw/sources/mcp-surfaces.md`; `kb/raw/sources/opencode-policy-and-runtime-plugins.md` | raw source notes | Added in the enrichment batch. |
| Planning manifests constrain sync and harness support claims. | `kb/raw/sources/planning-corpus-drift-source.md` | raw source note | Added after subagent gap audit. |
| Additional research coverage now maps hooks/evals, OpenSpec archive state, agent publication drift, risk-adjusted skill evals, and docs freshness gaps. | `kb/raw/sources/hooks-evals-control-source.md`; `kb/raw/sources/openspec-change-archive-source.md`; `kb/raw/sources/agent-publication-drift-coverage.md`; `kb/raw/sources/skill-catalog-risk-eval-coverage.md`; `kb/raw/sources/docs-artifact-freshness.md` | raw source notes | Added in autoresearch batch. |
| 2026-06-23 maximal enrichment adds catalog authoring, MCPHub, platform adapters, CI, scripts validation, and OpenSpec lifecycle sources. | `kb/raw/sources/skills-catalog-authoring-lifecycle-source.md`; `kb/raw/sources/mcphub-control-plane-source.md`; `kb/raw/sources/wagents-platform-adapters-source.md`; `kb/raw/sources/ci-release-workflows-source.md`; `kb/raw/sources/scripts-validation-tooling-source.md`; `kb/raw/sources/openspec-active-lifecycle-source.md` | raw source notes | Exhaustive-tier research batch. |
