---
title: Harness Surface Registry Capture W03
tags:
  - kb
  - raw
  - harness
  - registry
aliases:
  - Harness surface registry capture 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave03-config-2026-06-25
---

# Harness Surface Registry Capture W03

Read-only snapshot of `config/harness-surface-registry.json` and `config/support-tier-registry.json` on 2026-06-25.

## Fleet summary

| Metric | Value |
|--------|-------|
| Harness records | 19 |
| `validated` | 2 (`cursor-editor`, `cursor-cli`) |
| `repo-present-validation-required` | 15 |
| `experimental` | 2 (`perplexity-desktop`, `cherry-studio`) |

## Support tier vocabulary (`support-tier-registry.json`)

| Tier | Docs label | Promotion |
|------|------------|-----------|
| `validated` | Validated | allowed |
| `repo-present-validation-required` | Repo-present, validation required | blocked |
| `planned-research-backed` | Planned, research-backed | blocked |
| `experimental` | Experimental | blocked |
| `unverified` | Unverified | blocked |
| `unsupported` | Unsupported | blocked |
| `quarantine` | Quarantine | blocked (security lane) |

Rules: cannot mark `validated` without fixture + rollback; experimental/planned must not appear as supported in install commands; quarantine needs security-lane approval.

## Projection surface counts (across 19 harnesses)

| Surface | Harnesses claiming |
|---------|-------------------|
| `mcp` | 15 |
| `instructions` | 10 |
| `skills` | 9 |
| `agents` | 8 |
| `hooks` | 7 |
| `plugins` | 6 |
| `rules` | 2 |
| `cli-permissions` | 2 |
| `permissions` | 1 |
| `telemetry` | 1 |
| `bugbot-project-rules` | 1 |

## Owner-change clusters

| OpenSpec change | Harnesses |
|-----------------|-----------|
| `agents-c04-claude-harness` | claude-code, claude-desktop |
| `agents-c04-openai-harness` | chatgpt, codex |
| `agents-c04-copilot-harness` | github-copilot-web, github-copilot-cli |
| `agents-c04-opencode-gemini-harness` | opencode, gemini-cli, antigravity |
| `agents-c04-cursor-harness` | cursor-editor, cursor-cli, cursor-cloud-agent, cursor-cloud-subagent, cursor-bugbot, cursor-acp |
| `agents-c04-grok-harness` | grok-build |
| `agents-c04-experimental-harnesses` | perplexity-desktop, cherry-studio, crush |

## Notable caveats (selected)

- **cursor-editor / cursor-cli:** only project-local `.cursor` surfaces; global `~/.cursor` and dashboard state out of scope.
- **cursor-cloud-agent:** MCP/secrets dashboard-managed; narrower hook support than local Cursor.
- **chatgpt / claude-desktop / experimental desktops:** no default skill projection until verified.
- **grok-build:** skills CLI installs via claude-code alias; subagent depth capped at 1.

## Source notes

Generated from `planning/20-harness-registry/00-expanded-harness-surface-map.md` and `01-harness-projection-contract.md`. Registry records planning/support posture only — not an install manifest. Desktop, web/cloud, CLI, and editor variants are separate surfaces unless fixtures prove shared behavior.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Harness inventory and tiers | `config/harness-surface-registry.json` | canonical repo path |
| Tier vocabulary and rules | `config/support-tier-registry.json` | canonical repo path |
| Fixture posture cross-check | `planning/manifests/harness-fixture-support.json` | canonical repo path |