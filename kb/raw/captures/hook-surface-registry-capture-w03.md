---
title: Hook Surface Registry Capture W03
tags:
  - kb
  - raw
  - hooks
  - harness
aliases:
  - Hook surface registry capture 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave03-config-2026-06-25
---

# Hook Surface Registry Capture W03

Read-only snapshot of `config/hook-surface-registry.json` on 2026-06-25.

## Registry role

Dedicated per-harness hook discovery surfaces (file paths, embedding, authority). Complements `config/harness-surface-registry.json` (which lists `hooks` in `projection_surfaces`). Intended for `hook_scan.py`, `GapReport.hooks`, and harness discovery parity beyond file-presence checks.

## Fleet summary

| Metric | Value |
|--------|-------|
| Harnesses with hook surfaces declared | 9 |
| Harness aliases mapped | 28 alias keys → canonical ids |
| `kind` values | `hooks` \| `config` (embedded) |
| `role` values | `authoritative` \| `secondary` \| `repo-observed` \| `blind-spot` |

## Per-harness hook surfaces

| Harness | Authoritative paths | Notes |
|---------|---------------------|-------|
| `claude-code` | `.claude/settings.json`, `~/.claude/settings.json` | Embedded under `hooks` key |
| `codex` | `.codex/hooks.json`, `~/.codex/hooks.json` | Standalone hook files |
| `cursor-editor` | `.cursor/hooks.json`, `~/.cursor/hooks.json` | Project + global |
| `cursor-cloud-agent` | `.cursor/hooks.json` (secondary) | Not every local event supported in cloud |
| `gemini-cli` | `.gemini/settings.json`, `~/.gemini/settings.json` | Embedded hooks |
| `github-copilot-web` | `.github/hooks/*` (secondary) | Cloud policy on GitHub.com |
| `github-copilot-cli` | `.github/hooks/*` (secondary) | |
| `grok-build` | `~/.grok/hooks/*.json`, `config/grok-plannotator-hooks.json` (repo-observed) | Plannotator rendered on home sync |
| `opencode` | *(none)* | Plugin-internal hooks only |

## Blind spots (selected)

| Harness | Blind spot |
|---------|------------|
| `claude-code` | Claude managed policy / enterprise hooks |
| `cursor-editor`, `cursor-cloud-agent` | Cursor team hooks; cloud agent hook settings (dashboard) |
| `github-copilot-web` | GitHub.com / Copilot cloud hook policy |
| `opencode` | Plugin-internal hooks in `platforms/opencode/plugins/*`; no stable `hooks.json` |

## Alias normalization examples

`cursor` → `cursor-editor`; `cursor-agent` / `cursor-agent-cli` → `cursor-cli`; `copilot` / `github-copilot` → both web + CLI ids; `grok` / `grok-cli` → `grok-build`.

## Cross-registry note

`harness-surface-registry.json` lists `hooks` in `projection_surfaces` for 7 harnesses including `opencode`, but `hook-surface-registry.json` documents OpenCode as plugin-internal with empty `hook_surfaces` — discovery parity requires plugin-runtime scanning, not generic `hooks.json` presence.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Hook discovery surfaces | `config/hook-surface-registry.json` | canonical repo path |
| Hook render/merge | `config/hook-registry.json`, `scripts/sync_agent_stack.py` | canonical repo path |
| Platform adapters | `wagents/platforms/*.py` | canonical repo path |