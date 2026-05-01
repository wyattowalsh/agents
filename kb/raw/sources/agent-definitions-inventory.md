---
title: Agent Definitions Inventory
tags:
  - kb
  - source
  - agents
aliases:
  - Agent inventory source
kind: source-summary
status: active
updated: 2026-05-01
source_count: 1
---

# Agent Definitions Inventory

## Source Record

| Field | Value |
|-------|-------|
| source_id | `agent-definitions-inventory` |
| original_location | `agents/*.md`; `AGENTS.md`; `agent-bundle.json`; `wagents/rendering.py`; `tests/test_sync_agent_stack.py` |
| raw_path | `kb/raw/sources/agent-definitions-inventory.md` |
| capture_method | repo-local pointer summary from read-only inspection |
| captured_at | 2026-05-01 |
| size_bytes | pointer summary only |
| checksum | not captured |
| license_or_access_notes | repo-local canonical material |
| intended_wiki_coverage | [[agent-frontmatter-dialects]], [[agent-asset-model]], [[known-risks-and-open-gaps]] |

## Summary

The repo currently has eight agent definition files under `agents/`: orchestrator, code-reviewer, docs-writer, planner, researcher, security-auditor, release-manager, and performance-profiler. This creates a documentation drift point because `agent-bundle.json` has described `agents/` as reserved while the directory is actively populated.

Current agent files use fields aligned with OpenCode-style agent definitions, including `mode`, `temperature`, `color`, and `permission`, in addition to required name/description. The docs renderer expects the documented cross-platform fields when rendering catalog details, while tests enforce that repo-managed agent files avoid model selectors and step caps.

## Provenance

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| Eight agent definition files exist under `agents/`. | `agents/*.md` | canonical material | Inventory finding. |
| `agent-bundle.json` wording can drift from current populated agent directory. | `agent-bundle.json`; `agents/*.md` | canonical material | Open gap. |
| Current agent dialect is not identical to documented cross-platform table. | `AGENTS.md`; `agents/*.md`; `wagents/rendering.py` | canonical material | Synthesis page documents dialects. |
