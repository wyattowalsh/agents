# Harness Surfaces

## Contents

1. [Legend](#legend)
2. [Claude Code](#claude-code)
3. [Claude Desktop](#claude-desktop)
4. [ChatGPT](#chatgpt)
5. [Codex](#codex)
6. [GitHub Copilot Web](#github-copilot-web)
7. [GitHub Copilot CLI](#github-copilot-cli)
8. [Cursor](#cursor)
9. [Gemini CLI](#gemini-cli)
10. [Antigravity](#antigravity)
11. [OpenCode](#opencode)
12. [Perplexity Desktop](#perplexity-desktop)
13. [Cherry Studio](#cherry-studio)

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
| global | `~/.claude/CLAUDE.md` | authoritative | Global entrypoint |
| global | `~/.claude.json` | authoritative | User-level project registry and MCP/settings state |
| global | `~/.claude/settings.json` | authoritative | Global settings |
| global | `~/.claude/settings.local.json` | secondary | Local/global override surface |

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

## GitHub Copilot Web

| Scope | Surface | Role | Notes |
|-------|---------|------|-------|
| project | `.github/copilot-instructions.md` | authoritative | Generated in this repo; prefer canonical source when drift exists |
| project | `.github/instructions/**` | secondary | Additional generated guidance |
| project | `.github/hooks/**` | secondary | Generated hook scaffolding |
| project | `.vscode/mcp.json` | authoritative when present | Project MCP config used by Copilot surfaces that honor VS Code MCP |
| project | `platforms/copilot/agents/**` | secondary | Repo-managed auxiliary agent surfaces |
| project | `AGENTS.md` | secondary | Shared repo guidance |
| global | `~/.copilot/copilot-instructions.md` | secondary | Global instructions may affect local Copilot tools; GitHub.com settings remain separate |
| global | GitHub.com repository/org/Copilot coding agent settings | blind-spot | Web/cloud settings are not observable from local files by default |

Install agent name: `github-copilot`

## GitHub Copilot CLI

| Scope | Surface | Role | Notes |
|-------|---------|------|-------|
| project | `AGENTS.md` | secondary | Shared repo guidance |
| project | `.vscode/mcp.json` | secondary | Project MCP may be relevant when CLI uses VS Code/Copilot context |
| global | `~/.copilot/copilot-instructions.md` | authoritative | Global instructions |
| global | `~/.copilot/settings.json` | authoritative when present | CLI trusted folders and permissions |
| global | `~/.config/copilot-subagents.env` | authoritative when sourced | Global subagent fan-out caps |
| global | `~/.copilot/mcp-config.json` | authoritative when present | Global CLI MCP config |
| global | `~/.config/.copilot/mcp-config.json` | secondary | Alternate global MCP path |
| global | `~/.copilot/agents` | secondary | Installed/linked agents |

Install agent name: `github-copilot`

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

## Gemini CLI

| Scope | Surface | Role | Notes |
|-------|---------|------|-------|
| project | `GEMINI.md` | authoritative | Repo-local entrypoint |
| project | `AGENTS.md` | secondary | Shared guidance imported or referenced by wrapper files |
| project | `.gemini/settings.json` | authoritative when present | Project settings, MCP servers, and hooks |
| global | `~/.gemini/GEMINI.md` | authoritative | Global entrypoint |
| global | `~/.gemini/settings.json` | authoritative | Global settings, MCP servers, and hooks |
| global | `~/.gemini/skills` | secondary | Installed skill location |

Install agent name: `gemini-cli`

## Antigravity

| Scope | Surface | Role | Notes |
|-------|---------|------|-------|
| project | `GEMINI.md` | repo-observed | This repo treats Antigravity as a Gemini-style wrapper |
| project | `AGENTS.md` | repo-observed | Shared repo guidance |
| project | Native Antigravity project config | blind-spot | Not strongly verified from first-party docs in this plan |
| global | `~/.gemini/antigravity/mcp_config.json` | authoritative | First-party documented MCP config |
| global | `~/.gemini/antigravity/mcp_oauth_tokens.json` | secondary | Presence/permissions only; never read token values |
| global | `~/.gemini/extensions/outline-driven-development/antigravity/mcp_config.json` | secondary | Repo-observed extension path |
| global | Antigravity settings UI | blind-spot | First-party documented, not always file-backed locally |
| global | Antigravity agent mode settings | blind-spot | Approval/auto-exec/non-workspace file policies may live in the UI |

Install agent name: `antigravity`

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
