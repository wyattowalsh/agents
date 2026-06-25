---
title: Antigravity Crush Harness Capture W16
tags:
  - kb
  - source
  - external
  - antigravity
  - crush
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave16-pass2-2026-06-25
---

# Antigravity Crush Harness Capture W16

| Field | Value |
|-------|-------|
| source_id | `antigravity-crush-harness-capture-w16` |
| original_location | Root `GEMINI.md`; `Makefile` install targets; `README.md` supported agents |
| capture_method | repo bridge + Skills CLI adapter pointers |
| captured_at | 2026-06-25 |

## Summary

**Antigravity** and **Gemini CLI** share the `GEMINI.md` → `@./AGENTS.md` → `@instructions/global.md` bridge. **Crush** reads `AGENTS.md` → `@instructions/global.md` per `AGENTS.md` supported-agents table. Skills install: `make install-antigravity` / `make install-gemini` / `make install-crush` (Skills CLI `-a antigravity`, `gemini-cli`, `crush`).

## Harness registry

Both appear in `config/harness-surface-registry.json` as `repo-present-validation-required` tiers (not validated fixture tier). MCP projection follows MCPHub registry defaults unless a harness-specific plugin owner suppresses duplicates.

## Provenance

| Claim | Source |
|-------|--------|
| GEMINI bridge | `GEMINI.md`; `kb/raw/sources/external-harness-docs.md` |
| Install targets | `kb/raw/captures/makefile-dev-targets-capture-w13.md` |