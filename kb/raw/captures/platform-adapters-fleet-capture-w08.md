---
title: Platform Adapters Fleet Capture W08
tags:
  - kb
  - raw
  - platforms
  - sync
aliases:
  - Platform adapters fleet 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave08-platforms-2026-06-25
---

# Platform Adapters Fleet Capture W08

Read-only snapshot of `wagents/platforms/` on 2026-06-25. Line counts from `wc -l`; registry from `wagents/platforms/__init__.py`.

## Registry

| Identifier | Module | LOC | Implementation class |
|------------|--------|-----|----------------------|
| `claude-code` | `claude.py` | 142 | Native merge (settings, desktop MCP, hooks) |
| `codex` | `codex.py` | 46 | **Thin delegator** → `sync_agent_stack` codex helpers |
| `github-copilot` / `copilot` | `copilot.py` | 59 | **Thin delegator** → copilot generate/merge |
| `cursor` | `cursor.py` | 412 | Native project surfaces + home MCP merge |
| `gemini-cli` | `gemini.py` | 53 | Partial native (`render_hooks`) + monolith merge |
| `grok` | `grok.py` | 602 | **Native** TOML policy/MCP/skills/LSP/plannotator |
| `opencode` | `opencode.py` | 849 | **Native** JSON merge (largest adapter) |
| `vscode` | `vscode.py` | 114 | Native standard MCP JSON |
| `base.py` | shared | 667 | Merge helpers, `SyncContext`, MCPHub projection |

**Total Python LOC:** ~3004 across 10 modules. `get_adapter()` caches instances; `list_adapters()` → 9 identifiers; `available_adapters()` → 8 on capture host (`vscode` not installed).

## Interface contract (`PlatformAdapter`)

Each adapter implements:

- `repo_config_paths()` / `home_config_paths()` — discovery
- `render_mcp()` / `render_hooks()` — pure renderers (optional overrides)
- `sync_repo()` / `sync_home()` — impure entrypoints gated by `SyncContext.apply`

`SyncContext(apply=False)` enables dry-run; `assert_no_config_drops` guards merged home writes in base.

## Monolith coexistence

`scripts/sync_agent_stack.py` still owns bulk orchestration (~2900+ LOC) and imports `get_adapter()` for platform-filtered sync (`--platforms grok`, etc.). Codex/copilot/gemini adapters delegate `sync_*` to monolith functions rather than reimplementing merge logic.

## Adapter maturity tiers (implementation evidence)

| Tier | Adapters | Evidence |
|------|----------|----------|
| Native / substantial | grok, opencode, cursor, base | Dedicated merge/render logic in adapter modules |
| Hybrid | claude, vscode, gemini | Mix of adapter code + shared base helpers |
| Delegator | codex, copilot | `from scripts.sync_agent_stack import ...` only |

## Test coverage (selected)

| Test module | Focus |
|-------------|-------|
| `tests/test_platform_adapters.py` | Codex/copilot/gemini dry-run adapter smoke |
| `tests/test_grok_platform.py` | 31+ grok-specific adapter/sync tests |
| `tests/test_sync_agent_stack.py` | Monolith slices (`-k grok`, `-k opencode`, `-k codex`) |
| `tests/test_harness_rollback_fixtures.py` | Grok TOML merge-preservation rollback |

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Registry identifiers | `wagents/platforms/__init__.py` | canonical repo path |
| LOC counts | `wagents/platforms/*.py` | canonical repo paths |
| Delegation imports | `codex.py`, `copilot.py`, `gemini.py` | canonical repo paths |
| Monolith bridge | `scripts/sync_agent_stack.py` | canonical repo path |