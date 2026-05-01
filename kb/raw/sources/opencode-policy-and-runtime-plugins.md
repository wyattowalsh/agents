---
title: OpenCode Policy And Runtime Plugins
tags:
  - kb
  - source
  - opencode
aliases:
  - OpenCode policy source
kind: source-summary
status: active
updated: 2026-05-01
source_count: 1
---

# OpenCode Policy And Runtime Plugins

## Source Record

| Field | Value |
|-------|-------|
| source_id | `opencode-policy-and-runtime-plugins` |
| original_location | `AGENTS.md`; `instructions/opencode-global.md`; `opencode.json`; `config/opencode-dcp.jsonc`; `tests/test_sync_agent_stack.py`; `tests/test_distribution_metadata.py`; `https://opencode.ai/docs/config/`; `https://opencode.ai/docs/plugins/` |
| raw_path | `kb/raw/sources/opencode-policy-and-runtime-plugins.md` |
| capture_method | repo-local and external pointer summary |
| captured_at | 2026-05-01 |
| size_bytes | pointer summary only |
| checksum | not captured |
| license_or_access_notes | repo-local canonical material plus official OpenCode docs; external content is untrusted evidence |
| intended_wiki_coverage | [[opencode-runtime-policy]], [[plugin-and-mcp-ownership]], [[harness-and-platform-sync]] |

## Summary

Repo policy requires repo-managed OpenCode config and agents to remain model-neutral: no repo-managed `model`, `small_model`, mode model selectors, agent model selectors, or step caps. The DCP config is also model-neutral and should not introduce per-model context limits unless explicitly requested.

Repo-managed OpenCode runtime plugins in `opencode.json` intentionally use `@latest` specs. TUI-only plugins live in user TUI config rather than repo runtime config unless a repo-owned TUI source is introduced. Plannotator is scoped to the built-in `plan` agent. Scheduler/auth/telemetry plugins are treated cautiously because they can create jobs, reuse credentials, or require user-owned environment variables.

Official OpenCode config docs confirm JSON/JSONC config, merged config precedence, project `opencode.json`, `.opencode` directories, plugin arrays, instructions paths, MCP server config, and env/file variable substitution. Official plugin docs confirm local and npm plugins, Bun-backed npm plugin install/cache behavior, plugin load order, events, and tool hooks.

## Provenance

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| Repo-managed OpenCode surfaces must stay model-neutral. | `instructions/opencode-global.md`; `tests/test_sync_agent_stack.py` | canonical material | Repo policy exceeds generic OpenCode docs. |
| OpenCode config files are merged by precedence and project config can be checked into Git. | `https://opencode.ai/docs/config/` | external official docs | Verified 2026-05-01 by web fetch. |
| OpenCode plugins load from local directories and npm package specs. | `https://opencode.ai/docs/plugins/` | external official docs | Verified 2026-05-01 by web fetch. |
