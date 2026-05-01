---
title: Asset Validation Coverage
tags:
  - kb
  - source
  - validation
aliases:
  - Asset validator source
kind: source-summary
status: active
updated: 2026-05-01
source_count: 1
---

# Asset Validation Coverage

## Source Record

| Field | Value |
|-------|-------|
| source_id | `asset-validation-coverage` |
| original_location | `AGENTS.md`; `wagents/cli.py`; `skills/skill-creator/scripts/package.py`; `tests/test_package.py`; `tests/test_sync_agent_stack.py`; `wagents/rendering.py` |
| raw_path | `kb/raw/sources/asset-validation-coverage.md` |
| capture_method | repo-local pointer summary from read-only inspection |
| captured_at | 2026-05-01 |
| size_bytes | pointer summary only |
| checksum | not captured |
| license_or_access_notes | repo-local canonical material |
| intended_wiki_coverage | [[validation-and-test-coverage]], [[skill-authoring-and-validation]], [[agent-frontmatter-dialects]] |

## Summary

The repository has multiple validation gates with different strictness levels. `AGENTS.md` documents rich asset contracts. `wagents validate` enforces a minimal structural subset: required names/descriptions, kebab-case, directory or filename matching, skill body presence, and MCP directory shape. Packaging portability is stricter and checks fields such as `license`, `metadata.author`, and `metadata.version`, plus portable paths and referenced resources.

Agent frontmatter has an active dialect split. `AGENTS.md` documents cross-platform fields such as `tools`, `permissionMode`, `skills`, `mcpServers`, `memory`, and `hooks`, while current repo agent files use OpenCode-style fields including `mode`, `temperature`, `color`, and `permission`. Tests enforce that repo-managed agents remain model-neutral by rejecting `model:` and `steps:` fields.

## Provenance

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| `wagents validate` is less strict than package portability checks. | `wagents/cli.py`; `skills/skill-creator/scripts/package.py`; `tests/test_package.py` | canonical material | Validator and packaging gates have different acceptance bars. |
| Agent frontmatter currently includes OpenCode-style fields not listed in the base agent table. | `agents/*.md`; `AGENTS.md`; `wagents/rendering.py` | canonical material | Drift is documented, not resolved by this KB batch. |
| Tests enforce model-neutral repo-managed agent frontmatter. | `tests/test_sync_agent_stack.py` | canonical material | No code changed. |
