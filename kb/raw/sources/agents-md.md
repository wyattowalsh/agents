---
title: AGENTS.md Source Note
tags:
  - kb
  - source
aliases:
  - Repository Agent Standards Source
kind: source-summary
status: active
updated: 2026-05-01
source_count: 1
---

# AGENTS.md Source Note

## Source Record

| Field | Value |
|-------|-------|
| source_id | `agents-md` |
| original_location | `AGENTS.md` |
| raw_path | `kb/raw/sources/agents-md.md` |
| capture_method | Pointer summary from repo-local canonical file |
| captured_at | 2026-05-01 |
| size_bytes | not captured; source remains in place |
| checksum | not captured; source remains canonical in repo |
| license_or_access_notes | Repo-local tracked file |
| intended_wiki_coverage | [[agent-asset-model]], [[skill-authoring-and-validation]], [[harness-and-platform-sync]], [[openspec-workflow]] |

## Summary

`AGENTS.md` is the primary repository standard for asset formats, naming conventions, MCP conventions, bundle/plugin distribution, OpenSpec workflow, OpenCode configuration, Chrome DevTools MCP defaults, and supported agents. It defines the required frontmatter for skills and agents, where first-party MCP servers belong, and which surfaces are canonical versus generated.

## Provenance

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| Skills live at `skills/<name>/SKILL.md` and require `name` and `description` frontmatter. | `AGENTS.md` | canonical material | Asset format section. |
| Agents live at `agents/<name>.md` and require `name` and `description` frontmatter. | `AGENTS.md` | canonical material | Agent format section. |
| OpenSpec is required for non-trivial changes to public asset formats, downstream tooling, docs generation, sync behavior, validation behavior, or coordinated surfaces. | `AGENTS.md` | canonical material | OpenSpec workflow section. |
| Repo-managed OpenCode configuration should remain model-neutral by default. | `AGENTS.md` | canonical material | OpenCode DCP and plugin sections. |
