---
title: OpenCode Runtime Policy
tags:
  - kb
  - opencode
  - harness-sync
aliases:
  - OpenCode policy
kind: concept
status: active
updated: 2026-05-01
source_count: 3
---

# OpenCode Runtime Policy

## Scope

This page records repo-specific OpenCode policy and the official docs context behind it.

## Summary

Repo-managed OpenCode surfaces are deliberately model-neutral. Do not add repo-managed `model`, `small_model`, mode model selectors, agent model selectors, or step caps unless the user explicitly requests that class of change. Preserve live user-owned model settings when merging home config, but do not introduce repo defaults.

Repo `opencode.json` is the runtime plugin surface. Its npm plugin specs intentionally use `@latest`, and Plannotator is scoped to the built-in `plan` agent. Scheduler, auth, and telemetry plugins need caution because they can create scheduled work, reuse credentials, or require user-owned environment variables.

Official OpenCode docs confirm config merge precedence, project `opencode.json`, `.opencode` directories, plugin arrays, local/npm plugins, plugin load order, instruction path arrays, MCP config, and env/file substitution. This repo's stricter model-neutral policy is local governance layered on top of the generic OpenCode config model.

## Evidence

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| Repo-managed OpenCode config and agents must remain model-neutral. | `kb/raw/sources/opencode-policy-and-runtime-plugins.md`; `instructions/opencode-global.md` | raw source note + canonical material | Hard repo policy. |
| OpenCode config files are merged by precedence. | `kb/raw/sources/opencode-policy-and-runtime-plugins.md`; `kb/raw/sources/external-harness-docs.md` | external source notes | Official OpenCode docs. |
| Plugins can be loaded from npm or local directories. | `kb/raw/sources/opencode-policy-and-runtime-plugins.md` | external source note | Official OpenCode plugin docs. |

## Related

- [[harness-and-platform-sync]]
- [[plugin-and-mcp-ownership]]
- [[canonical-generated-surfaces]]
