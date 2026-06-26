---
title: "Research journal — KB wave 08"
tags:
  - kb
  - raw
  - journal
  - provenance
aliases:
  - "KB wave 08 journal"
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave08-platforms-2026-06-25
original_location: "~/.grok/research/kb-wave08-platforms-2026-06-25.md"
---

# Research journal — KB wave 08

- **Goal:** `goals/kb-research-ingest/goal.md`
- **Wave:** 08 | Theme: platforms instructions and harness config templates
- **Captured:** 2026-06-25
- **Commit message:** `feat(kb): wave 08 — platforms instructions and harness config templates`

## G0 brief

Read-only ingest of `instructions/*`, `wagents/platforms/*`, and harness config templates (`config/grok-config.toml`, `config/codex-config.toml`, `opencode.json` metadata; no secrets).

## Ownership map

| Role | Artifact | Path |
|------|----------|------|
| worker | `harness-config-templates-capture-w08` | `kb/raw/captures/harness-config-templates-capture-w08.md` |
| worker | `instructions-hierarchy-capture-w08` | `kb/raw/captures/instructions-hierarchy-capture-w08.md` |
| worker | `opencode-platform-adapter-capture-w08` | `kb/raw/captures/opencode-platform-adapter-capture-w08.md` |
| worker | `platform-adapters-fleet-capture-w08` | `kb/raw/captures/platform-adapters-fleet-capture-w08.md` |

## Ingest queue

- `raw`: added 4 captures (`instructions-hierarchy-capture-w08`, `platform-adapters-fleet-capture-w08`, `harness-config-templates-capture-w08`, `opencode-platform-adapter-capture-w08`).

## Capture evidence (excerpts)

### `harness-config-templates-capture-w08`

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

### `instructions-hierarchy-capture-w08`

# Instructions Hierarchy Capture W08

Read-only inventory of `instructions/*` and harness instruction mirrors on 2026-06-25. Metadata only — no live home config paths read.

## Canonical fleet (`instructions/`)

| File | Bytes | Pattern | Role |
|------|-------|---------|------|
| `global.md` | 8158 | SSOT | Cross-platform operating rules (trust boundaries, OpenSpec, skills install) |
| `codex-global.md` | 9079 | **full generated copy** | Codex entrypoint; duplicates `global.md` body + Codex overrides (no `@` import) |
| `opencode-global.md` | 13088 | `@global` + overrides | OpenCode runtime/plugin/model policy (largest bridge) |
| `grok-global.md` | 4314 | `@global` + overrides | Grok config surfaces, LSP, subagent depth, Plannotator |
| `gemini-cli-global.md` | 1488 | `@global` + overrides | Gemini tool-efficiency and fleet dispatch |
| `copilot-global.md` | 963 | `@global` + overrides | Copilot fleet/model policy |
| `opencode-agents-overlay.md` | 3936 | overlay only | OpenCode-only agent frontmatter (`mode`, `temperature`, etc.) |
| `claude-code-global.md` | 105 | `@global` shim | Points active configs at `global.md` |

Five of six platform bridges import `global.md` via `@./instructions/global.md`. `codex-global.md` is the exception: sync generates a standalone file symlinked to `~/.codex/AGENTS.md`.

## Harness mirrors (downstream projections)

| Surface | Count | Notes |
|---------|-------|-------|
| `.github/instructions/*.instructions.md` | 14 | Copilot workspace instructions |
| `.apm/instructions/*.instructions.md` | 14 | APM package compile targets |
| `.cursor/rules/*.mdc` | includes `codex`, `grok`, `opencode` overlays | Cursor rule injection |
| `opencode.json` `instructions` array | 3 paths | `AGENTS.md`, `opencode-global.md`, `opencode-agents-overlay.md` |

APM materialization mapping (`wagents/apm.py`): `codex-global.md` → `codex.instructions.md`, `grok-global.md` → `grok.instructions.md`, `opencode-global.md` → `opencode.instructions.md`.

## Sync-manifest modes (selected)

| Path | Mode |
|------|------|

### `opencode-platform-adapter-capture-w08`

# OpenCode Platform Adapter Capture W08

Read-only capture of `wagents/platforms/opencode.py`, `opencode.json`, and instruction linkage on 2026-06-25.

## Adapter scope (849 LOC)

Handles repo + home OpenCode surfaces:

| Surface | Path | Role |
|---------|------|------|
| Home runtime | `~/.config/opencode/opencode.json` | MCP, providers, instructions, skills, plugins merge |
| Repo project | `${REPO_ROOT}/opencode.json` | Project runtime mirror |
| Satellite configs | `config/opencode-*.json(c)` → home copies | DCP, ensemble, quota-toast, token-monitor, octto, large-image-optimizer |
| TUI | `~/.config/opencode/tui.json` | User-owned; template `config/opencode-tui-plugins.json` |
| Local plugins | `~/.config/opencode/plugins/` | Repo `./plugins/*.mjs` deployment |

Instruction constants in adapter: `OPENCODE_GLOBAL_MD`, `OPENCODE_AGENTS_OVERLAY_MD`, `GLOBAL_MD`.

## Repo `opencode.json` metadata

| Key | Capture value | Notes |
|-----|---------------|-------|
| Top-level keys | 16 | Includes `$schema`, `model`, `small_model`, `plugin`, `mcp`, `provider`, `formatter`, `lsp`, `experimental` |
| `instructions` | 3 paths | `AGENTS.md`, `opencode-global.md`, `opencode-agents-overlay.md` |
| `model` | `openai/gpt-5.5` | Repo-managed default (policy exception documented in `opencode-global.md`) |
| `plugin` array | 40 entries | Mix of `@latest` npm specs + 3 local `./plugins/*.mjs` |
| Local plugin specs | 3 | `opencode-context-cache.mjs`, `octto-primary-inherit.mjs`, `opencode-incomplete-resume.mjs` |

## Merge policy highlights (adapter code)

- Strips managed provider IDs on every write: `vercel`, `opencode-go`, `kimi-for-coding`
- Sanitizes `xai.options` to `{}` to prevent invalid provider option accumulation
- `_RUNTIME_DEFAULT_KEYS` managed set includes `model`, `formatter`, `lsp`, `experimental`, `permission`
- TUI-only plugin keys tracked separately; `_DISABLED_TUI_PLUGIN_KEYS` documents known conflicts (tree-sitter worker path)

### `platform-adapters-fleet-capture-w08`

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


## Key findings

Derived from command-backed captures above; canonical repo files remain authoritative.

## Metrics

**net-new raw sources: 4**; pages enriched: 3; lint: pass (0 issues).

## Gate status

- G1 research: complete (read-only repo paths / external pointers)
- G2 ingest: captures written under `kb/raw/`
- G3 enrich: wiki/index updates per wave manifest
- G4 audit: `uv run python skills/nerdbot/scripts/kb_lint.py --root kb --fail-on warning` exit 0 before wave commit
