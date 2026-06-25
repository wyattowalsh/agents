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
updated: 2026-06-25
source_count: 4
---

# Wagents Platform Adapters

## Summary

Harness sync projects repo assets into per-platform surfaces through `scripts/sync_agent_stack.py` and adapters under `wagents/platforms/` (base, cursor, codex, grok, opencode, copilot, gemini, vscode). `SyncContext(apply=False)` enables dry-run and `--check` drift reporting without mutation.

**2026-06-25 fleet snapshot (Wave 08):** nine registered identifiers in `wagents/platforms/__init__.py` (~3004 LOC). Native implementations: **grok** (602 LOC, TOML policy/MCP/skills/LSP), **opencode** (849 LOC, JSON merge + satellite configs), **cursor** (412 LOC, project surfaces). Thin delegators to the monolith: **codex** (46 LOC), **copilot** (59 LOC), **gemini** (53 LOC with custom `render_hooks`). `get_adapter()` is cached; `available_adapters()` reflects installed home paths (vscode often absent).

Implemented safety includes refusing config drops on merged home globals, merge helpers that preserve user-owned MCP/hook entries, and limited `.bak` backups for symlink replacement. Declared rollback requirements in `config/config-transaction-registry.json` are not fully implemented for every merged path.

## Why it matters

- Platform-specific behavior (Cursor overlays, Grok skill mirroring, OpenCode plugin merges) lives here, not only in `AGENTS.md`.
- Support-tier and fixture manifests gate how aggressively to claim harness validation.
- Legacy monolith and adapters coexist; changes must consider both call paths.

## Current shape

| Adapter / surface | LOC | Notes |
|-------------------|-----|-------|
| `wagents/platforms/base.py` | 667 | Merge helpers, config-drop guards, MCPHub projection, `SyncContext` |
| `wagents/platforms/cursor.py` | 412 | Agent overlays from `config/cursor-agents.json`; six Cursor harness rows |
| `wagents/platforms/grok.py` | 602 | `config/grok-config.toml` policy merge; plannotator; skill mirror; MCP blocks |
| `wagents/platforms/opencode.py` | 849 | `opencode.json` + `config/opencode-*` templates; provider scrub |
| `wagents/platforms/codex.py` | 46 | Delegates to `merge_codex_config`, `merge_codex_hooks` in monolith |
| `wagents/platforms/copilot.py` | 59 | Delegates repo/home copilot generate + merge helpers |
| `wagents/platforms/claude.py` | 142 | Settings/hooks/desktop MCP merge |
| `wagents/platforms/gemini.py` | 53 | Symlink entrypoint + `merge_gemini_settings` |
| `wagents/platforms/vscode.py` | 114 | Repo-local standard MCP JSON |
| `scripts/sync_agent_stack.py` | ~2900+ | Orchestrator; calls `get_adapter()` for `--platforms` filters |
| `config/sync-manifest.json` | — | Managed paths and modes (canonical/generated/merged) |

## Implementation maturity

| Tier | Adapters | Implication |
|------|----------|-------------|
| Native | grok, opencode, cursor | Prefer adapter module when changing merge behavior |
| Hybrid | claude, vscode, gemini | Adapter + base helpers; partial monolith calls |
| Delegator | codex, copilot | Changes still land in `sync_agent_stack.py` until migrated |

## Config template pairing

| Harness | Repo template | Instruction bridge | Adapter |
|---------|---------------|-------------------|---------|
| grok-build | `config/grok-config.toml` (canonical) | `instructions/grok-global.md` | `grok.py` |
| codex | `config/codex-config.toml` (generated) | `instructions/codex-global.md` | `codex.py` |
| opencode | `opencode.json` + `config/opencode-*.json(c)` | `opencode-global.md`, overlay | `opencode.py` |

## Constraints and edge cases

- Cursor repo sync writes project-local surfaces; global `~/.cursor` may differ.
- Copilot uses a separate agent corpus under `platforms/copilot/agents/` (11 files vs 8 canonical).
- Codex/copilot adapters are thin wrappers — fixture tests may exercise monolith paths, not adapter-only code.
- Rollback fixtures: grok/codex/opencode `present`; many other harnesses `planned` (see [[harness-fixture-gaps]]).

## Provenance

| Claim or section | Raw or canonical material | Notes |
|------------------|---------------------------|-------|
| Adapter inventory and safety | `kb/raw/sources/wagents-platform-adapters-source.md` | Primary pointer |
| 2026-06-25 fleet LOC/registry | `kb/raw/captures/platform-adapters-fleet-capture-w08.md` | Wave 08 capture |
| Config template pairing | `kb/raw/captures/harness-config-templates-capture-w08.md` | Metadata only |
| Transaction registry contract | `kb/raw/sources/config-registries-and-sync.md` | Rollback gap |
| Fixture manifest snapshot | `kb/raw/captures/harness-fixture-capture-w01.md`; `planning/manifests/harness-fixture-support.json` | Planning evidence |

## Related wiki pages

- [[sync-transaction-safety]]
- [[harness-fixture-gaps]]
- [[harness-and-platform-sync]]
- [[opencode-runtime-policy]]
- [[agent-publication-and-drift-coverage]]

## Open questions

- When platform adapters fully subsume `sync_agent_stack.py` monolith paths (codex/copilot/gemini delegators remain).
- Whether vscode adapter warrants fixture promotion given repo-local-only scope.