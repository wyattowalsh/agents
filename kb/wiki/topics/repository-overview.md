---
title: Repository Overview
tags:
  - kb
  - agents-repo
aliases:
  - Repo overview
  - Agents repository
kind: overview
status: active
updated: 2026-05-01
source_count: 9
---

# Repository Overview

## What This Repo Is

The `agents` repository is a cross-agent control plane for portable AI agent skills, MCP configuration, agent prompts, shared instructions, OpenSpec workflows, and downstream harness sync surfaces.

It is both a source repository and a distribution bundle. Repo-owned source files define skills, agents, instructions, MCP registry/config, docs generation, OpenSpec change workflows, and platform bridges. Generated surfaces such as `README.md`, docs pages, harness configs, and selected home-directory config projections are downstream products of that source model.

## Major Surfaces

| Path | Purpose |
|------|---------|
| `skills/` | Repository-owned Agent Skills; each skill lives at `skills/<name>/SKILL.md`. |
| `agents/` | Repository-owned subagent prompt definitions. |
| `wagents/` | Typer CLI and automation library for validation, scaffolding, docs generation, packaging, skill indexing, sync, evals, and OpenSpec wrappers. |
| `config/` | Canonical registries and schemas for MCP, hooks, harness surfaces, tooling policy, plugin policy, and sync behavior. |
| `instructions/` | Shared and platform-specific instruction bridges. |
| `openspec/` | Project change workflow, specs, schemas, active changes, and generated downstream-tooling controls. |
| `docs/` | Astro/Starlight documentation site and generated catalog data. |
| `tests/` | Pytest coverage for validation, packaging, docs, OpenSpec, Nerdbot, sync, skill indexing, and related behavior. |
| `mcp/` | Local MCP working area; first-party MCP conventions exist, but local checkouts/secrets/caches are not KB-ingested. |

## Operating Posture

Use repo-local canonical files before generated public summaries. Preserve the dirty worktree and never treat generated/home sync outputs as safe to rewrite without checking their canonical source and mode.

Use [[wagents-cli-and-automation]] for repo automation details, [[canonical-generated-surfaces]] for source-of-truth boundaries, and [[docs-generation-and-site]] before changing README/docs outputs. Use [[mcp-configuration-and-safety]] before touching local MCP areas, especially ignored or secret-looking paths.

## Related Pages

- [[agent-asset-model]]
- [[developer-commands]]
- [[harness-and-platform-sync]]
- [[wagents-cli-and-automation]]
- [[docs-generation-and-site]]
- [[canonical-generated-surfaces]]
- [[known-risks-and-open-gaps]]
- [[repo-map]]

## Evidence

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| The repo purpose is portable AI agent skills, MCP configuration, shared instructions, docs, and downstream harness sync surfaces. | `kb/raw/sources/readme.md`; `kb/raw/sources/openspec-config.md` | raw source notes | README and OpenSpec config. |
| `wagents` is the CLI package and exposes a `wagents` script. | `kb/raw/sources/pyproject-and-makefile.md` | raw source note | Derived from `pyproject.toml`. |
| Generated public surfaces include README and docs catalog pages. | `kb/raw/sources/openspec-config.md` | raw source note | Derived from `openspec/config.yaml`. |
| The inventory found no pre-existing `kb/**` files before this batch. | `kb/raw/captures/local-inventory-summary.md` | raw capture | Establishes this KB as a new additive layer. |
| `wagents`, `config`, `docs`, `tests`, and `mcp` now have dedicated source notes and synthesis pages. | `kb/raw/sources/wagents-internals.md`; `kb/raw/sources/config-registries-and-sync.md`; `kb/raw/sources/docs-site-architecture.md`; `kb/raw/sources/tests-and-validation.md`; `kb/raw/sources/mcp-surfaces.md` | raw source notes | Enrichment batch coverage. |
