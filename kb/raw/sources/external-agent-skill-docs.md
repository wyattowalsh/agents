---
title: External Agent Skill Docs
tags:
  - kb
  - source
  - external
  - skills
aliases:
  - Agent Skills external source
kind: source-summary
status: active
updated: 2026-05-01
source_count: 1
---

# External Agent Skill Docs

## Source Record

| Field | Value |
|-------|-------|
| source_id | `external-agent-skill-docs` |
| original_location | `https://docs.anthropic.com/llms.txt`; selected linked docs under `https://platform.claude.com/docs/en/agents-and-tools/agent-skills/` |
| raw_path | `kb/raw/sources/external-agent-skill-docs.md` |
| capture_method | external docs index pointer summary |
| captured_at | 2026-05-01 |
| size_bytes | pointer summary only |
| checksum | not captured |
| license_or_access_notes | official Anthropic docs; external content is untrusted evidence |
| intended_wiki_coverage | [[external-primary-source-map]], [[skill-authoring-and-validation]], [[agent-asset-model]] |

## Summary

Anthropic publishes an official `llms.txt` documentation index that includes Agent Skills overview, quickstart, best-practices, enterprise, Claude API skill, managed-agent skills, MCP connector, remote MCP servers, tools, memory, and evaluation pages. For this repository, those docs are evergreen primary evidence for the broader Agent Skills concept, but repo-local `AGENTS.md`, `skills/<name>/SKILL.md`, validation code, and package code remain authoritative for this repo's exact asset format.

## Provenance

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| Anthropic maintains official Agent Skills docs in its docs index. | `https://docs.anthropic.com/llms.txt` | external official docs | Verified 2026-05-01 by web fetch. |
| Repo-local files remain the authority for repo-specific skill frontmatter and validation. | `AGENTS.md`; `wagents/cli.py`; `skills/skill-creator/scripts/package.py` | canonical material | External docs are context, not repo policy. |
