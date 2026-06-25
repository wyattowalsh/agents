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
updated: 2026-06-25
source_count: 5
---

# OpenCode Runtime Policy

## Scope

This page records repo-specific OpenCode policy and the official docs context behind it.

## Summary

Repo-managed OpenCode surfaces are deliberately model-neutral for **agent frontmatter**: do not add repo-managed `model`, `small_model`, mode model selectors, agent model selectors, or step caps to canonical `agents/*.md`. Runtime-specific keys live in `instructions/opencode-agents-overlay.md` and load only under the OpenCode harness.

**Exception (documented):** root `opencode.json` and home `~/.config/opencode/opencode.json` carry repo-managed `model` / `small_model` defaults (`openai/gpt-5.5`, `openai/gpt-5.4-mini`) per `instructions/opencode-global.md`. The adapter strips transient provider blocks (`vercel`, `opencode-go`, `kimi-for-coding`) and resets `xai.options` to `{}` on every merge write.

Repo `opencode.json` is the runtime plugin surface. Its npm plugin specs intentionally use `@latest` (40 entries in the 2026-06-25 capture), and Plannotator is scoped to the built-in `plan` agent. Scheduler, auth, and telemetry plugins need caution because they can create scheduled work, reuse credentials, or require user-owned environment variables.

Official OpenCode docs confirm config merge precedence, project `opencode.json`, `.opencode` directories, plugin arrays, local/npm plugins, plugin load order, instruction path arrays, MCP config, and env/file substitution. This repo's stricter frontmatter model-neutral policy is local governance layered on top of the generic OpenCode config model.

## Adapter surfaces (2026-06-25)

| Surface | Repo source | Home target |
|---------|-------------|-------------|
| Runtime JSON | `opencode.json` | `~/.config/opencode/opencode.json` |
| Instructions | `AGENTS.md`, `opencode-global.md`, overlay | Merged `instructions` array |
| DCP / ensemble / quota / octto | `config/opencode-*.json(c)` | Matching home paths under `~/.config/opencode/` |
| Local plugins | `./plugins/*.mjs` (3 specs) | `~/.config/opencode/plugins/` |
| TUI | template only | `~/.config/opencode/tui.json` (user-owned) |

`wagents/platforms/opencode.py` (849 LOC) owns merge logic; monolith still orchestrates `--platforms opencode` filtering.

## Instruction linkage

| File | Role |
|------|------|
| `instructions/opencode-global.md` | Largest platform bridge (13 KB); plugin, formatter, LSP, session-poisoning policy |
| `instructions/opencode-agents-overlay.md` | OpenCode-only agent keys (`mode`, `temperature`, `color`, `permission`) |
| `instructions/global.md` | Imported via `@./instructions/global.md` in opencode-global |

Downstream mirrors: `.github/instructions/opencode.instructions.md`, `.apm/instructions/opencode.instructions.md`, `.cursor/rules/opencode.mdc`.

## Fixture posture

`planning/manifests/harness-fixture-support.json` marks **opencode** as `fixture-executable` with `rollback_coverage: present`. Validation commands include `test_distribution_metadata.py`, `wagents validate`, and `test_platform_adapters.py`. Promotion to `validated` tier blocked on CI matrix green — same bar as codex.

## Evidence

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| Agent frontmatter model-neutral; root config exception | `kb/raw/sources/opencode-policy-and-runtime-plugins.md`; `instructions/opencode-global.md` | raw source + canonical | Hard repo policy |
| Adapter merge paths and plugin count | `kb/raw/captures/opencode-platform-adapter-capture-w08.md` | raw capture | Wave 08 |
| Instruction array and overlay split | `kb/raw/captures/instructions-hierarchy-capture-w08.md` | raw capture | Wave 08 |
| OpenCode config files are merged by precedence | `kb/raw/sources/external-harness-docs.md` | external source note | Official OpenCode docs |
| Plugins can be loaded from npm or local directories | `kb/raw/sources/opencode-policy-and-runtime-plugins.md` | external source note | Official OpenCode plugin docs |
| Fixture tier and rollback | `planning/manifests/harness-fixture-support.json` | canonical repo path | Executable, not validated |

## Related

- [[harness-and-platform-sync]]
- [[plugin-and-mcp-ownership]]
- [[canonical-generated-surfaces]]
- [[wagents-platform-adapters]]
- [[harness-fixture-gaps]]