---
title: Docs Artifact Freshness
tags:
  - kb
  - source
  - docs
  - generated
aliases:
  - Docs freshness source
  - Docs artifact source
kind: source-summary
status: active
updated: 2026-05-01
source_count: 1
---

# Docs Artifact Freshness

## Source Record

| Field | Value |
|-------|-------|
| source_id | `docs-artifact-freshness` |
| original_location | `config/docs-artifact-registry.json`; `config/schemas/docs-artifact-registry.schema.json`; `wagents/docs.py`; `wagents/cli.py`; `wagents/site_model.py`; `tests/test_docs.py`; `tests/test_readme.py`; `docs/src/content/docs/`; `docs/src/generated-site-data.mjs`; `docs/src/generated-sidebar.mjs`; `planning/65-docs-and-instructions/`; `openspec/changes/agents-c08-docs-instructions/validation-matrix.md` |
| raw_path | `kb/raw/sources/docs-artifact-freshness.md` |
| capture_method | repo-local pointer summary from read-only research with non-mutating freshness checks reported by subagent |
| captured_at | 2026-05-01 |
| size_bytes | pointer summary only |
| checksum | not captured |
| license_or_access_notes | repo-local docs, registry, tests, and planning material |
| intended_wiki_coverage | [[docs-generation-and-site]], [[known-risks-and-open-gaps]], [[canonical-generated-surfaces]] |

## Summary

The docs artifact registry records a subset of generated docs surfaces and their validation commands. README freshness has a non-mutating check through `uv run wagents readme --check`, but docs generation lacks a matching `wagents docs generate --check` command. The generator rewrites more surfaces than the current registry lists, including generated skill, agent, MCP, CLI, external-skill, index, data, and sidebar artifacts.

Read-only research found current generated site data and generated skill/agent page counts aligned with source counts, but also identified a concrete hand-maintained docs drift: the MCP docs index says 34 configured servers while `mcp.json` and generated site data report 30.

## Provenance

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| The docs artifact registry tracks generated docs artifacts and validation commands, but only for a subset of surfaces. | `config/docs-artifact-registry.json`; `config/schemas/docs-artifact-registry.schema.json` | canonical config and schema | Registry scope evidence. |
| `wagents docs generate` rewrites generated content, indexes, CLI docs, site data, and sidebar data. | `wagents/docs.py`; `wagents/cli.py`; `wagents/site_model.py`; `tests/test_docs.py` | implementation and tests | Write-oriented generator. |
| README has a non-mutating freshness check. | `tests/test_readme.py`; `wagents/cli.py` | tests and CLI implementation | `uv run wagents readme --check`. |
| Current generated site data and generated skill/agent page counts were reported fresh by the read-only research pass. | `docs/src/generated-site-data.mjs`; `docs/src/generated-sidebar.mjs`; `docs/src/content/docs/skills/`; `docs/src/content/docs/agents/` | generated surfaces | Research finding; full docs build not run. |
| The hand-maintained MCP docs index appears stale against current configured server count. | `docs/src/content/docs/mcp/index.mdx`; `mcp.json`; `docs/src/generated-site-data.mjs` | docs and generated data | Concrete docs drift gap. |
