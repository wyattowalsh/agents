---
title: Scripts Validate Collectors Capture W12
tags:
  - kb
  - raw
  - validation
aliases:
  - Validate collectors 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave12-gap-sweep-2026-06-25
---

# Scripts Validate Collectors Capture W12

Read-only inventory of `scripts/validate/` on 2026-06-25. Explicit path listing; no repo-wide globs.

## Layout

| Path | Role |
|------|------|
| `scripts/validate/validate_repo.py` | Aggregator; `collect_repo_errors()` merges collector outputs |
| `scripts/validate/collectors/skills.py` | Skill frontmatter + asset_toolkit validation |
| `scripts/validate/collectors/agents.py` | Agent conventions subprocess |
| `scripts/validate/collectors/mcp.py` | MCP package surfaces |
| `scripts/validate/collectors/mcp_registry.py` | MCP registry contributor policy |
| `scripts/validate/collectors/hooks.py` | Hook policy surfaces |
| `scripts/validate/collectors/paths.py` | Path portability |
| `scripts/validate/collectors/quarantine.py` | Catalog index + legacy external-skills quarantine dual-read |
| `scripts/validate/_toolkit.py` | asset_toolkit import bootstrap |
| `scripts/check_agent_stack.py` | `sync_main(["--check", "--targets", "all"])` wrapper |
| `scripts/validate_codex_config.py` | Codex TOML schema check (orphaned from CI) |

Collector module count: **7** Python modules under `collectors/` (excluding `__init__.py`).

## ty/ruff scope note

`scripts/validate/**` is excluded from `[tool.ty.src]` and has `[tool.ruff.lint.per-file-ignores]` `E402` for runtime `sys.path` bootstrap.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Module list | `scripts/validate/collectors/*.py` | canonical repo |
| Aggregator | `scripts/validate/validate_repo.py` | canonical repo |
| Prior summary | `kb/raw/sources/scripts-validation-tooling-source.md` | raw source note |