---
title: Wagents Platform Adapters
tags:
  - kb
  - sync
  - platforms
aliases:
  - Platform adapters
kind: concept
status: active
updated: 2026-06-23
source_count: 2
---

# Wagents Platform Adapters

## Summary

Harness sync projects repo assets into per-platform surfaces through `scripts/sync_agent_stack.py` and adapters under `wagents/platforms/` (base, cursor, codex, grok, opencode, copilot, gemini, vscode). `SyncContext(apply=False)` enables dry-run and `--check` drift reporting without mutation.

Implemented safety includes refusing config drops on merged home globals, merge helpers that preserve user-owned MCP/hook entries, and limited `.bak` backups for symlink replacement. Declared rollback requirements in `config/config-transaction-registry.json` are not fully implemented for every merged path.

## Why it matters

- Platform-specific behavior (Cursor overlays, Grok skill mirroring, OpenCode plugin merges) lives here, not only in `AGENTS.md`.
- Support-tier and fixture manifests gate how aggressively to claim harness validation.
- Legacy monolith and adapters coexist; changes must consider both call paths.

## Current shape

| Adapter / surface | Notes |
|-------------------|-------|
| `wagents/platforms/base.py` | Merge helpers, config-drop guards, MCP namespace rules |
| `wagents/platforms/cursor.py` | Agent overlays from `config/cursor-agents.json` |
| `wagents/platforms/grok.py` | Config + plannotator + skill mirror paths |
| `wagents/platforms/opencode.py` | Runtime config merges, DCP/TUI handling |
| `scripts/sync_agent_stack.py` | Orchestrator for repo + home targets |
| `config/sync-manifest.json` | Managed paths and modes (canonical/generated/merged) |

## Constraints and edge cases

- Cursor repo sync writes project-local surfaces; global `~/.cursor` may differ.
- Copilot uses a separate agent corpus under `platforms/copilot/agents/` (11 files vs 8 canonical).
- Rollback fixtures remain mostly `planned` in `planning/manifests/harness-fixture-support.json`.

## Provenance

| Claim or section | Raw or canonical material | Notes |
|------------------|---------------------------|-------|
| Adapter inventory and safety | `kb/raw/sources/wagents-platform-adapters-source.md` | Primary |
| Transaction registry contract | `kb/raw/sources/config-registries-and-sync.md` | Rollback gap |
| Fixture manifest snapshot | `kb/raw/sources/planning-corpus-drift-source.md` | Planning evidence |

## Related wiki pages

- [[sync-transaction-safety]]
- [[harness-fixture-gaps]]
- [[harness-and-platform-sync]]
- [[agent-publication-and-drift-coverage]]

## Open questions

- When platform adapters fully subsume `sync_agent_stack.py` monolith paths.