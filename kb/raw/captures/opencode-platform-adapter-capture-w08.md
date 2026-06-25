---
title: OpenCode Platform Adapter Capture W08
tags:
  - kb
  - raw
  - opencode
  - platforms
aliases:
  - OpenCode adapter capture 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave08-platforms-2026-06-25
---

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
- `assert_no_config_drops` used on home merges

## Model-neutral policy tension (documented)

`instructions/opencode-global.md` states repo-managed model defaults **and** agent frontmatter must avoid `model`/`small_model` selectors. `opencode.json` carries root model keys by explicit repo exception; canonical `agents/*.md` stay portable — overlay in `opencode-agents-overlay.md`.

## Fixture posture (`harness-fixture-support.json`)

| Field | Value |
|-------|-------|
| `harness_id` | `opencode` |
| `fixture_status` | `fixture-executable` |
| `rollback_coverage` | `present` |
| `fixture_classes` | model-neutral-policy, plugin-placement, dcp, credential-guard, rollback |
| `validation_commands` | `test_distribution_metadata.py`, `wagents validate`, `test_platform_adapters.py` |
| `promotion_blocker` | CI matrix green before `validated` tier |

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Adapter paths and merge keys | `wagents/platforms/opencode.py` | canonical repo path |
| Runtime JSON shape | `opencode.json` | canonical repo path |
| Instruction policy | `instructions/opencode-global.md` | canonical repo path |
| Fixture tier | `planning/manifests/harness-fixture-support.json` | canonical repo path |