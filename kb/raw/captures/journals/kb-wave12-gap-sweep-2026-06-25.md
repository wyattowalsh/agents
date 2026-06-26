---
title: "Research journal — KB wave 12"
tags:
  - kb
  - raw
  - journal
  - provenance
aliases:
  - "KB wave 12 journal"
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave12-gap-sweep-2026-06-25
original_location: "~/.grok/research/kb-wave12-gap-sweep-2026-06-25.md"
---

# Research journal — KB wave 12

- **Goal:** `goals/kb-research-ingest/goal.md`
- **Wave:** 12 | Theme: collectors and harness policy templates
- **Captured:** 2026-06-25
- **Commit message:** `feat(kb): wave 12 — collectors and harness policy templates`

## G0 brief

Explicit-path captures for validate collectors (7 modules), Grok/Codex policy templates, and Starlight astro.config plugin stack.

## Ownership map

| Role | Artifact | Path |
|------|----------|------|
| worker | `harness-policy-templates-capture-w12` | `kb/raw/captures/harness-policy-templates-capture-w12.md` |
| worker | `scripts-validate-collectors-capture-w12` | `kb/raw/captures/scripts-validate-collectors-capture-w12.md` |
| worker | `starlight-astro-config-capture-w12` | `kb/raw/captures/starlight-astro-config-capture-w12.md` |

## Ingest queue

- `raw`: added 3 captures (`scripts-validate-collectors-capture-w12`, `harness-policy-templates-capture-w12`, `starlight-astro-config-capture-w12`).

## Capture evidence (excerpts)

### `harness-policy-templates-capture-w12`

# Harness Policy Templates Capture W12

Metadata-only capture from repo-managed harness policy templates on 2026-06-25. No credential values, no live home config bodies.

## `config/grok-config.toml` (repo template)

| Section | Notable keys |
|---------|--------------|
| `[models]` | `default = grok-composer-2.5-fast`; `web_search = grok-4.20-multi-agent` |
| `[ui]` | `permission_mode = always-approve`; fork secondary model |
| `[features]` | `lsp_tools`, `codebase_indexing`; telemetry/feedback disabled |
| `[subagents]` | enabled; explore/plan toggles; depth cap in repo policy |
| `[plugins].paths` | Repo plugin path placeholders (resolved on home sync) |

Sync: `scripts/sync_agent_stack.py --apply --platforms grok` → `~/.grok/config.toml`; project MCP in `.grok/config.toml`.

## `config/codex-config.toml` (repo template)

| Key | Value |
|-----|-------|
| `model` | `gpt-5.5` |
| `model_reasoning_effort` | `xhigh` |
| `web_search` | `live` |
| `sandbox_mode` | `danger-full-access` |
| `[features]` | hooks, plugins, multi_agent, shell_tool, tool_search, … |
| MCP | Projected from `config/mcp-registry.json` via sync (names only in KB) |

Schema: `#:schema https://developers.openai.com/codex/config-schema.json`

## Distinct surfaces

| Harness | Repo SSOT | Home/live target |
|---------|-----------|------------------|
| Grok | `config/grok-config.toml` | `~/.grok/config.toml` |

### `scripts-validate-collectors-capture-w12`

# Scripts Validate Collectors Capture W12

Read-only inventory of `scripts/validate/` on 2026-06-25. Explicit path listing; no repo-wide globs.

## Layout

| Path | Role |
|------|------|
| `scripts/validate/validate_repo.py` | Aggregator; `collect_repo_errors()` merges collector outputs |
| `scripts/validate/collectors/skills.py` | Skill frontmatter + asset_toolkit validation |
| `scripts/validate/collectors/agents.py` | Agent conventions subprocess |
| `scripts/validate/collectors/mcp.py` | MCP package surfaces |
| `scripts/validate/collectors/mcp_registry.py` | MCP registry contributor policy |
| `scripts/validate/collectors/hooks.py` | Hook policy surfaces |
| `scripts/validate/collectors/paths.py` | Path portability |
| `scripts/validate/collectors/quarantine.py` | Catalog index + legacy external-skills quarantine dual-read |
| `scripts/validate/_toolkit.py` | asset_toolkit import bootstrap |
| `scripts/check_agent_stack.py` | `sync_main(["--check", "--targets", "all"])` wrapper |
| `scripts/validate_codex_config.py` | Codex TOML schema check (orphaned from CI) |

Collector module count: **7** Python modules under `collectors/` (excluding `__init__.py`).

## ty/ruff scope note

`scripts/validate/**` is excluded from `[tool.ty.src]` and has `[tool.ruff.lint.per-file-ignores]` `E402` for runtime `sys.path` bootstrap.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Module list | `scripts/validate/collectors/*.py` | canonical repo |
| Aggregator | `scripts/validate/validate_repo.py` | canonical repo |
| Prior summary | `kb/raw/sources/scripts-validation-tooling-source.md` | raw source note |

### `starlight-astro-config-capture-w12`

# Starlight Astro Config Capture W12

Read-only capture from `docs/astro.config.mjs` on 2026-06-25. Aligns with upstream Starlight `starlight()` integration documented in `external-tooling-docs`.

## Integration stack

| Piece | Config |
|-------|--------|
| Framework | Astro `defineConfig` with `output: 'server'`, Vercel adapter |
| Starlight | `starlight({ title, description, sidebar: generatedSidebar, … })` |
| Plugins | `starlightThemeBlack`, `starlightLinksValidator`, `starlightLlmsTxt` (`rawContent: true`) |
| Generated inputs | `./src/generated-sidebar.mjs`, `./src/generated-site-data.mjs` |
| CSS | Tailwind via Vite plugin + token/base/component stylesheets |

## CI/docs gate pairing

Docs job runs `wagents docs generate --no-installed` before Astro check/build. Starlight sidebar is generator-owned (`wagents docs generate`), not hand-edited in committed pages.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Plugin array and options | `docs/astro.config.mjs` | canonical repo |
| Upstream Starlight model | `https://starlight.astro.build/reference/configuration/` | external docs |
| Prior architecture | `kb/raw/sources/docs-site-architecture.md` | raw source note |


## Key findings

Derived from command-backed captures above; canonical repo files remain authoritative.

## Metrics

**net-new raw sources: 3**; pages enriched: 3; lint: pass (exit 0).

## Gate status

- G1 research: complete (read-only repo paths / external pointers)
- G2 ingest: captures written under `kb/raw/`
- G3 enrich: wiki/index updates per wave manifest
- G4 audit: `uv run python skills/nerdbot/scripts/kb_lint.py --root kb --fail-on warning` exit 0 before wave commit
