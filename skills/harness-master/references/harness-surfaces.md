# Harness Surfaces

## Contents

1. [Legend](#legend)
2. [Claude Code](#claude-code)
3. [Claude Desktop](#claude-desktop)
4. [ChatGPT](#chatgpt)
5. [Codex](#codex)
6. [Cursor](#cursor)
7. [Grok Build](#grok-build)
8. [OpenCode](#opencode)
9. [Perplexity Desktop](#perplexity-desktop)
10. [Cherry Studio](#cherry-studio)

## Legend

- **authoritative** - best current evidence says this surface directly controls behavior
- **secondary** - adjacent or fallback surface that may still matter
- **generated** - should usually be changed indirectly via a canonical source
- **merged** - local file may contain managed and unmanaged content
- **repo-observed** - observed from this repository's sync/generation logic, not necessarily first-party documented
- **blind-spot** - not observable from the current filesystem/session

## Claude Code

| Scope | Surface | Role | Notes |
|-------|---------|------|-------|
| project | `AGENTS.md` | secondary | Repo-wide guidance shared across tools |
| project | `CLAUDE.md` | authoritative | Claude Code entrypoint for repo-local guidance |
| project | `.claude/rules/*.md` | secondary | File-scoped or path-scoped rules |
| project | `.mcp.json` | authoritative when present | Claude Code project MCP surface |
| project | `.claude/settings.json` | authoritative when present | Project settings surface |
| project | `.claude/settings.local.json` | secondary | Local project overrides when present |
| project | `.claude/settings.json` (embedded hooks) | authoritative | Hooks surface (embedded in settings; explicit `kind: hooks` surface emitted by discover in addition to config) |
| project | `.claude/settings.local.json` (embedded hooks) | secondary | Local overrides may embed hooks |
| global | `~/.claude/CLAUDE.md` | authoritative | Global entrypoint |
| global | `~/.claude.json` | authoritative | User-level project registry and MCP/settings state |
| global | `~/.claude/settings.json` | authoritative | Global settings |
| global | `~/.claude/settings.local.json` | secondary | Local/global override surface |
| global | `~/.claude/settings.json` (embedded hooks) | authoritative | Hooks surface (embedded in settings; explicit `kind: hooks`) |
| global | `~/.claude/settings.local.json` (embedded hooks) | secondary | Local/global hooks overrides |

Install agent name: `claude-code`

## Claude Desktop

| Scope | Surface | Role | Notes |
|-------|---------|------|-------|
| global | `~/Library/Application Support/Claude/claude_desktop_config.json` | authoritative | Desktop app local MCP config; merged by this repo's sync script |

Install agent name: N/A (desktop app config only)

## ChatGPT

| Scope | Surface | Role | Notes |
|-------|---------|------|-------|
| global | `~/Library/Application Support/ChatGPT/mcp.json` | repo-observed | Desktop MCP config merged by this repo; official connector flow is UI/HTTPS-first |
| global | ChatGPT Apps and Connectors settings | blind-spot | Developer-mode connector state is UI-managed unless exported through another channel |

Install agent name: N/A (desktop/web app config only)

## Codex

| Scope | Surface | Role | Notes |
|-------|---------|------|-------|
| project | `AGENTS.md` | authoritative | Codex reads repo docs from `AGENTS.md` |
| project | `.codex/config.toml` | authoritative when present | Project config applies only in trusted projects |
| global | `~/.codex/AGENTS.md` | authoritative | Global entrypoint |
| global | `~/.codex/config.toml` | authoritative | Global config |
| global | `~/.codex/skills` | secondary | Installed skill location |

Install agent name: `codex`

## Cursor

| Scope | Surface | Role | Notes |
|-------|---------|------|-------|
| project | `AGENTS.md` | authoritative or secondary | Simple instruction path; compare with `.cursor/rules/**` |
| project | nested `AGENTS.md` | secondary | More specific directory-scoped instructions |
| project | `.cursor/rules/*.md` / `.cursor/rules/*.mdc` | authoritative when present | Project rules system |
| project | `.cursor/mcp.json` | authoritative when present | Project MCP config |
| project | `.cursor/skills/**/SKILL.md` | authoritative when present | Cursor-native project skills |
| project | `.agents/skills/**/SKILL.md` | secondary | Compatibility skills directory |
| project | `.cursor/agents/*.md` | authoritative when present | Cursor subagents |
| project | `.cursor/hooks.json` | authoritative when present | Project hooks; cloud agents may also run repo hooks |
| project | `.cursor/cli.json` | authoritative when present | Project CLI permissions/settings |
| project | `.cursorignore` | authoritative when present | Files excluded from Cursor context |
| global | `~/.cursor/mcp.json` | authoritative | Global MCP config |
| global | `~/.cursor/permissions.json` | authoritative, medium confidence | Still referenced by current docs but newer CLI docs also use CLI config |
| global | `~/.cursor/cli-config.json` | authoritative | CLI global config |
| global | `~/.cursor/hooks.json` | authoritative when present | User hooks |
| global | `~/.cursor/skills` | authoritative when present | Cursor-native global skills |
| global | `~/.agents/skills` | secondary | Compatibility global skills directory |
| global | `~/.cursor/agents/*.md` | authoritative when present | Global Cursor subagents |
| global | Cursor user rules in settings UI | blind-spot | UI-managed unless exported |
| global | Team rules/dashboard | blind-spot | Org-managed, not observable from local files |
| global | Cloud Agent settings/secrets/API state | blind-spot | Dashboard/API-managed web surfaces |
| global | Team/Enterprise hooks | blind-spot | Admin-distributed hooks may not be local files |

Install agent name: `cursor`

## Grok Build

| Scope | Surface | Role | Notes |
|-------|---------|------|-------|
| project | `config/grok-plannotator-hooks.json` | repo-observed | Canonical policy for Plannotator plan-mode hooks (PreToolUse for enter/exit); rendered on sync to global hooks dir |
| global | `~/.grok/hooks/*.json` | authoritative | Grok hook surfaces (directory of JSON hook files); includes plannotator.json when synced via repo Grok plannotator install |
| global | `~/.grok/hooks/plannotator.json` | authoritative (when present) | Rendered Plannotator hooks (exit_plan_mode -> block/deny shim + context improvement) |

Grok Build also observes shared `AGENTS.md` / `instructions/grok-global.md` and MCP via the common sync pipeline (see harness-surface-registry for other projection surfaces).

Install agent name: `grok-build`

## OpenCode

| Scope | Surface | Role | Notes |
|-------|---------|------|-------|
| project | `AGENTS.md` | authoritative | OpenCode reads `AGENTS.md` directly |
| project | `opencode.json` | authoritative | Native config surface |
| project | `.opencode/agents/*.md` | secondary | Repo-native OpenCode-specific agents |
| project | `.opencode/ocx.jsonc` | repo-observed | Repo-local OpenCode companion config when present |
| project | `platforms/opencode/plugins/*` | secondary | Repo-managed plugin sources synced to global plugins dir |
| global | `~/.config/opencode/opencode.json` | authoritative | Global config |
| global | `~/.config/opencode/AGENTS.md` | secondary | Global instruction surface when present |
| global | `~/.config/opencode/skills` | secondary | Repo-observed global skills path from local OpenCode conventions |
| global | `~/.config/opencode/plugins/*` | secondary | Global plugin files |
| global | Global OpenCode rules | blind-spot | A stable first-party global rules path is not verified in this plan |

Install agent name: `opencode`

## Perplexity Desktop

| Scope | Surface | Role | Notes |
|-------|---------|------|-------|
| project | `.perplexity/skills/*.md` | repo-observed | Repo-managed skill files; official filesystem loading is not verified |
| global | `~/.perplexity/skills/*.md` | repo-observed | Synced by this repo when present |
| global | Perplexity Mac app Connectors UI | blind-spot | Local MCP connectors are configured in the app UI |
| global | Perplexity Computer Skills UI/storage | blind-spot | Custom skills are official, but local filesystem path is not first-party verified here |

Install agent name: N/A (desktop app config only)

## Cherry Studio

| Scope | Surface | Role | Notes |
|-------|---------|------|-------|
| project | `.cherry/presets/*.json` | repo-observed | Repo-managed presets copied into Cherry Studio support dir |
| global | `~/Library/Application Support/CherryStudio/config.json` | authoritative | App settings merged by `merge_cherry_studio_config()` |
| global | `~/Library/Application Support/CherryStudio/mcp-import/managed/*.json` | generated | MCP import packs managed by `render_cherry_import_files()` |
| global | `~/Library/Application Support/CherryStudio/presets/*.json` | repo-observed | Copied presets; not direct MCP state |
| global | Cherry Studio UI settings | blind-spot | App state such as selected model/theme may only be observable through the UI |

Install agent name: N/A (desktop app)
