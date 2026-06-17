# Proposal

## Problem

Catalog pages were being mechanically trimmed (`summary` density, line caps) instead of composed with standardized frontmatter and curated bodies.

## Intent

Standardize frontmatter across harness-integrated surfaces (skills, agents, MCP, hooks, configs) and compose each page via orchestrator waves using researcher/docs-steward subagents. Generator scaffolds and preserves composed pages.

## Supersedes

`openspec/changes/docs-copy-reduction/` trimming intent (density defaults reverted to `standard`).

## Validation

- `uv run wagents docs compose --write-manifest`
- `uv run wagents docs generate --no-installed`
- `uv run pytest tests/test_page_density.py tests/test_docs_compose.py tests/test_rendering.py`
- `uv run wagents docs build`
