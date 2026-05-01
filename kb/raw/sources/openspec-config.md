---
title: OpenSpec Config Source Note
tags:
  - kb
  - source
  - openspec
aliases:
  - OpenSpec source
kind: source-summary
status: active
updated: 2026-05-01
source_count: 2
---

# OpenSpec Config Source Note

## Source Record

| Field | Value |
|-------|-------|
| source_id | `openspec-config` |
| original_location | `openspec/config.yaml`; `AGENTS.md` |
| raw_path | `kb/raw/sources/openspec-config.md` |
| capture_method | Pointer summary from repo-local canonical files |
| captured_at | 2026-05-01 |
| size_bytes | not captured; sources remain in place |
| checksum | not captured; sources remain canonical in repo |
| license_or_access_notes | Repo-local tracked files |
| intended_wiki_coverage | [[openspec-workflow]], [[developer-commands]], [[known-risks-and-open-gaps]] |

## Summary

`openspec/config.yaml` states the repository context, primary source-of-truth files, generated public surfaces, supported downstream agents, OpenSpec tool mapping, telemetry policy, model-neutral OpenCode policy, and proposal/design/validation/task rules.

## Provenance

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| Primary source-of-truth files include `AGENTS.md`, `instructions/global.md`, `skills/`, `agents/`, `mcp.json`, `config/`, `agent-bundle.json`, and `openspec/`. | `openspec/config.yaml` | canonical material | Context lines. |
| Generated public surfaces include README from `uv run wagents readme` and docs catalog pages from `uv run wagents docs generate`. | `openspec/config.yaml` | canonical material | Context lines. |
| OpenSpec wrappers should be used for AI-readable JSON and set `OPENSPEC_TELEMETRY=0` unless opted in. | `openspec/config.yaml`; `AGENTS.md` | canonical material | Context and OpenSpec workflow sections. |
