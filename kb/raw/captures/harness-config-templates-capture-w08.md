---
title: Harness Config Templates Capture W08
tags:
  - kb
  - raw
  - config
  - grok
  - codex
aliases:
  - Harness config templates 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave08-platforms-2026-06-25
---

# Harness Config Templates Capture W08

Metadata-only capture of repo-managed harness config templates on 2026-06-25. **No secret values, bearer tokens, or live `~/.codex` / `~/.grok` paths ingested.**

## Fleet summary

| Template | Path | Lines | Tables | Sync-manifest mode | Home target |
|----------|------|-------|--------|-------------------|-------------|
| Grok policy | `config/grok-config.toml` | 88 | 19 | `canonical` | `~/.grok/config.toml` (managed policy block) |
| Codex policy | `config/codex-config.toml` | 259 | 34 | `generated` | `~/.codex/config.toml` (merge) |
| OpenCode runtime | `opencode.json` | 826+ | N/A (JSON) | repo root generated | `~/.config/opencode/opencode.json` |

OpenCode has **no** `config/opencode-config.toml`; runtime policy is JSON plus satellite templates under `config/opencode-*.json(c)`.

## Grok policy template (`config/grok-config.toml`)

**Purpose:** Sanitized repo SSOT merged into home `config.toml` via `wagents/platforms/grok.py` managed block `GROK_POLICY_BEGIN/END`.

| Section prefix | Merge mode (adapter) | Policy intent |
|----------------|---------------------|---------------|
| `models`, `telemetry`, `compat`, `plugins`, `mcp_servers` | replace-owned | Repo defaults for models and compat layers |
| `ui`, `features`, `session`, `tools`, `toolset`, `subagents`, `memory` | blend-owned | Preserve user tweaks where possible |

Notable tables (names only): `models`, `ui`, `ui.notifications`, `features`, `session`, `subagents`, `memory.*`, `compat.cursor`, `compat.claude`.

Repo template does **not** embed managed MCP blocks; MCP projection uses separate `GROK_MCP_BEGIN/END` markers at sync time.

Paired instruction SSOT: `instructions/grok-global.md` (canonical). Env-only toggles: `config/grok-env.sh`.

## Codex policy template (`config/codex-config.toml`)

**Purpose:** Generated repo mirror of Codex home config shape; merged on home sync by `merge_codex_config`.

Top-level keys (metadata): `approval_policy`, `sandbox_mode`, `model`, `model_reasoning_effort`, `web_search`, `features.*` (hooks/plugins/multi_agent enabled).

Managed block:

```
# BEGIN MANAGED BY sync_agent_stack.py: MCP_SERVERS
… 15 × [mcp_servers.<name>] tables …
# END MANAGED BY sync_agent_stack.py: MCP_SERVERS
```

MCP entries use MCPHub `remote-stdio.sh` with `127.0.0.1:46683` endpoints — **server names recorded, no credentials captured.**

Profiles present: `deep`, `fast`, `full_access` (table names only).

Paired instruction: `instructions/codex-global.md` (generated, symlinked to `~/.codex/AGENTS.md`).

## OpenCode note (cross-reference)

OpenCode model/plugin defaults live in `opencode.json` (`model`, `small_model`, `plugin` array). See `opencode-platform-adapter-capture-w08.md` for adapter merge paths and plugin count.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Line/table counts | `config/grok-config.toml`, `config/codex-config.toml` | canonical repo paths |
| Sync-manifest modes | `config/sync-manifest.json` | canonical repo path |
| Grok merge prefixes | `wagents/platforms/grok.py` | canonical repo path |
| MCP block boundaries | `config/codex-config.toml` | canonical repo path |