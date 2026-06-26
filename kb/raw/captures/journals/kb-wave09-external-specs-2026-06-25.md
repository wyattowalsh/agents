---
title: "Research journal — KB wave 09"
tags:
  - kb
  - raw
  - journal
  - provenance
aliases:
  - "KB wave 09 journal"
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave09-external-specs-2026-06-25
original_location: "~/.grok/research/kb-wave09-external-specs-2026-06-25.md"
---

# Research journal — KB wave 09

- **Goal:** `goals/kb-research-ingest/goal.md`
- **Wave:** 09 | Theme: external Agent Skills and MCP spec indexes
- **Captured:** 2026-06-25
- **Commit message:** `feat(kb): wave 09 — external Agent Skills and MCP spec indexes`

## G0 brief

Fetched `agentskills.io/llms.txt` and `modelcontextprotocol.io/llms.txt`; stub + extract for portable skills spec index.

## Ownership map

| Role | Artifact | Path |
|------|----------|------|
| worker | `agentskills-llms-index-extract-w09` | `kb/raw/extracts/agentskills-llms-index-extract-w09.md` |
| worker | `agentskills-spec-capture-w09` | `kb/raw/sources/agentskills-spec-capture-w09.md` |
| worker | `mcp-spec-index-capture-w09` | `kb/raw/sources/mcp-spec-index-capture-w09.md` |

## Ingest queue

- `raw`: added 2 sources + 1 extract (`agentskills-spec-capture-w09`, `mcp-spec-index-capture-w09`, `agentskills-llms-index-extract-w09`).

## Capture evidence (excerpts)

### `agentskills-llms-index-extract-w09`

# Agent Skills LLMS Index Extract W09

Normalized extract from `https://agentskills.io/llms.txt` (2026-06-25).

## Document links

| Topic | URL |
|-------|-----|
| Overview | https://agentskills.io/home.md |
| Specification | https://agentskills.io/specification.md |
| Best practices | https://agentskills.io/skill-creation/best-practices.md |
| Evaluating skills | https://agentskills.io/skill-creation/evaluating-skills.md |
| Optimizing descriptions | https://agentskills.io/skill-creation/optimizing-descriptions.md |
| Quickstart | https://agentskills.io/skill-creation/quickstart.md |
| Using scripts | https://agentskills.io/skill-creation/using-scripts.md |
| Client implementation | https://agentskills.io/client-implementation/adding-skills-support.md |
| Client showcase | https://agentskills.io/clients.md |

## Use in KB

Context for portable skill format comparisons; not repo policy.

### `agentskills-spec-capture-w09`

# Agent Skills Spec Capture W09

External primary source: [agentskills.io](https://agentskills.io/) documentation index.

## Source Record

| Field | Value |
|-------|-------|
| source_id | `agentskills-spec-capture-w09` |
| original_location | `https://agentskills.io/llms.txt`; `https://agentskills.io/specification.md` |
| raw_path | `kb/raw/sources/agentskills-spec-capture-w09.md` |
| capture_method | llms.txt index fetch + specification pointer |
| captured_at | 2026-06-25 |
| intended_wiki_coverage | [[external-primary-source-map]], [[skill-authoring-and-validation]] |

## Quoted index entries

> [Specification](https://agentskills.io/specification.md): The complete format specification for Agent Skills.

> [Best practices for skill creators](https://agentskills.io/skill-creation/best-practices.md): How to write skills that are well-scoped and calibrated to the task.

## Summary

agentskills.io documents the cross-platform Agent Skills format (YAML frontmatter + markdown body, discovery semantics). Repo `AGENTS.md` and `skills/*/SKILL.md` remain authoritative for this repository's extensions and validation.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| llms.txt index | `https://agentskills.io/llms.txt` | external fetch |
| Repo format authority | `kb/raw/sources/agents-md.md` | canonical pointer |

### `mcp-spec-index-capture-w09`

# MCP Spec Index Capture W09

External primary source: [modelcontextprotocol.io](https://modelcontextprotocol.io/) documentation index.

## Source Record

| Field | Value |
|-------|-------|
| source_id | `mcp-spec-index-capture-w09` |
| original_location | `https://modelcontextprotocol.io/llms.txt`; spec `2025-11-25` tree |
| raw_path | `kb/raw/sources/mcp-spec-index-capture-w09.md` |
| capture_method | llms.txt index fetch |
| captured_at | 2026-06-25 |
| intended_wiki_coverage | [[external-primary-source-map]], [[mcp-configuration-and-safety]] |

## Quoted index entries

> [What is the Model Context Protocol (MCP)?](https://modelcontextprotocol.io/docs/getting-started/intro.md)

> [Tools](https://modelcontextprotocol.io/specification/2025-11-25/server/tools.md)

> [Security Best Practices](https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices.md)

## Summary

MCP llms.txt indexes specification (2025-11-25), SDK docs, registry publishing, extensions (apps, auth, tasks), and security tutorials. Repo `config/mcp-registry.json` and MCPHub remain authoritative for local control-plane behavior.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| llms.txt index | `https://modelcontextprotocol.io/llms.txt` | external fetch |
| Local MCP policy | `kb/raw/sources/mcp-surfaces.md` | repo pointer |


## Key findings

Derived from command-backed captures above; canonical repo files remain authoritative.

## Metrics

**net-new raw sources: 3**; pages enriched: 2; lint: pass.

## Gate status

- G1 research: complete (read-only repo paths / external pointers)
- G2 ingest: captures written under `kb/raw/`
- G3 enrich: wiki/index updates per wave manifest
- G4 audit: `uv run python skills/nerdbot/scripts/kb_lint.py --root kb --fail-on warning` exit 0 before wave commit
