---
title: Agent Bundle And Sync Source Note
tags:
  - kb
  - source
aliases:
  - Bundle and sync source
kind: source-summary
status: active
updated: 2026-05-01
source_count: 3
---

# Agent Bundle And Sync Source Note

## Source Record

| Field | Value |
|-------|-------|
| source_id | `agent-bundle-and-sync` |
| original_location | `agent-bundle.json`; `config/sync-manifest.json`; `opencode.json` |
| raw_path | `kb/raw/sources/agent-bundle-and-sync.md` |
| capture_method | Pointer summary from repo-local config files |
| captured_at | 2026-05-01 |
| size_bytes | not captured; sources remain in place |
| checksum | not captured; sources remain canonical/generated in repo |
| license_or_access_notes | Repo-local tracked files; may include absolute local paths in sync manifests |
| intended_wiki_coverage | [[harness-and-platform-sync]], [[agent-asset-model]], [[known-risks-and-open-gaps]] |

## Summary

`agent-bundle.json` is the cross-agent bundle manifest for skills, agents, MCP servers, instructions, and OpenSpec. `config/sync-manifest.json` records canonical, generated, symlinked, and merged surfaces across repo and home paths. `opencode.json` is the repo-managed OpenCode configuration with instructions, skill path, OpenTelemetry flag, plugin array, and canvas permission.

## Provenance

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| The bundle maps `skills`, `agents`, `mcpServers`, `instructions`, and `openspec` components. | `agent-bundle.json` | canonical material | Components object. |
| OpenSpec package and tool mapping are declared in the bundle adapter. | `agent-bundle.json` | canonical material | OpenSpec adapter object. |
| Sync manifest distinguishes canonical, generated, symlink, and merged surfaces. | `config/sync-manifest.json` | canonical material | Managed entries. |
| OpenCode loads `AGENTS.md` and `instructions/opencode-global.md`, uses `skills` as the skill path, and keeps plugin specs at `@latest`. | `opencode.json`; `AGENTS.md` | canonical/generated material | OpenCode config plus repo policy. |
