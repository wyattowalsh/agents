# Harness Surfaces

## Contents

1. [Legend](#legend)
2. [Claude Code](#claude-code)
3. [Codex](#codex)
4. [Cursor](#cursor)
5. [Gemini CLI](#gemini-cli)
6. [Antigravity](#antigravity)
7. [GitHub Copilot](#github-copilot)
8. [OpenCode](#opencode)

## Legend

- **authoritative** — best current evidence says this surface directly controls behavior
- **secondary** — adjacent or fallback surface that may still matter
- **generated** — should usually be changed indirectly via a canonical source
- **merged** — local file may contain managed and unmanaged content
- **blind-spot** — not observable from the current filesystem/session

## Claude Code

| Scope | Surface | Role | Notes |
|-------|---------|------|-------|
| project | `AGENTS.md` | secondary | Repo-wide guidance shared across tools |
| project | `CLAUDE.md` | authoritative | Claude entrypoint for repo-local guidance |
| project | `.claude/rules/*.md` | secondary | File-scoped or path-scoped rules |
| project | `.claude/settings.json` | authoritative when present | Project settings surface |
| project | `.claude/settings.local.json` | secondary | Local project overrides when present |
| global | `~/.claude/CLAUDE.md` | authoritative | Global entrypoint |
| global | `~/.claude/settings.json` | authoritative | Global settings |
| global | `~/.claude/settings.local.json` | secondary | Local/global override surface |
| global | `~/Library/Application Support/Claude/claude_desktop_config.json` | secondary | Desktop app MCP/config adjacency |

Install agent name: `claude-code`

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
| global | `~/.cursor/mcp.json` | authoritative | Global MCP config |
| global | `~/.cursor/permissions.json` | authoritative | Global auto-run allowlists |
| global | Cursor settings user rules | blind-spot | UI-managed unless exported |
| global | Team rules/dashboard | blind-spot | Org-managed, not observable from local files |

Install agent name: `cursor`

## Gemini CLI

| Scope | Surface | Role | Notes |
|-------|---------|------|-------|
| project | `GEMINI.md` | authoritative | Repo-local entrypoint |
| project | `AGENTS.md` | secondary | Shared guidance imported or referenced by wrapper files |
| project | `.gemini/settings.json` | authoritative when present | Project settings |
| global | `~/.gemini/GEMINI.md` | authoritative | Global entrypoint |
| global | `~/.gemini/settings.json` | authoritative | Global settings |
| global | `~/.gemini/skills` | secondary | Installed skill location |

Install agent name: `gemini-cli`

## Antigravity

| Scope | Surface | Role | Notes |
|-------|---------|------|-------|
| project | `GEMINI.md` | repo-observed | This repo treats Antigravity as a Gemini-style wrapper |
| project | `AGENTS.md` | repo-observed | Shared repo guidance |
| project | Native Antigravity project config | blind-spot | Not strongly verified from first-party docs in this plan |
| global | `~/.gemini/antigravity/mcp_config.json` | authoritative | First-party documented MCP config |
| global | `~/.gemini/extensions/outline-driven-development/antigravity/mcp_config.json` | secondary | Repo-observed extension path |
| global | Antigravity settings UI | blind-spot | First-party documented, not always file-backed locally |
| global | Antigravity agent mode settings | blind-spot | Approval/auto-exec policy may live in the UI |

Install agent name: `antigravity`

## GitHub Copilot

| Scope | Surface | Role | Notes |
|-------|---------|------|-------|
| project | `.github/copilot-instructions.md` | authoritative | Generated in this repo; prefer canonical source when drift exists |
| project | `.github/instructions/**` | secondary | Additional generated guidance |
| project | `.github/hooks/**` | secondary | Generated hook scaffolding |
| project | `.vscode/mcp.json` | authoritative when present | Project MCP config |
| project | `platforms/copilot/agents/**` | secondary | Repo-managed auxiliary agent surfaces |
| project | `AGENTS.md` | secondary | Shared repo guidance |
| global | `~/.copilot/copilot-instructions.md` | authoritative | Global instructions |
| global | `~/.copilot/settings.json` | authoritative when present | Global settings |
| global | `~/.config/copilot-subagents.env` | authoritative when sourced | Global subagent fan-out caps |
| global | `~/.copilot/mcp-config.json` | authoritative when present | Global MCP config |
| global | `~/.config/.copilot/mcp-config.json` | secondary | Alternate global MCP path |
| global | `~/.copilot/agents` | secondary | Installed/linked agents |

Install agent name: `github-copilot`

## OpenCode

| Scope | Surface | Role | Notes |
|-------|---------|------|-------|
| project | `AGENTS.md` | authoritative | OpenCode reads `AGENTS.md` directly |
| project | `opencode.json` | authoritative | Native config surface |
| project | `.opencode/agents/*.md` | secondary | Repo-native OpenCode-specific agents |
| project | `.opencode/ocx.jsonc` | repo-observed | Repo-local OpenCode companion config when present |
| global | `~/.config/opencode/opencode.json` | authoritative | Global config |
| global | `~/.config/opencode/AGENTS.md` | secondary | Global instruction surface when present |
| global | `~/.config/opencode/skills` | secondary | Repo-observed global skills path from local OpenCode conventions |
| global | Global OpenCode rules | blind-spot | A stable first-party global rules path is not verified in this plan |

Install agent name: `opencode`

## Cherry Studio

| Scope | Surface | Role | Notes |
|-------|---------|------|-------|
| global | `~/Library/Application Support/CherryStudio/config.json` | authoritative | App settings (synced via `merge_cherry_studio_config()`) |
| global | `~/Library/Application Support/CherryStudio/mcp-import/managed/*.json` | generated | MCP imports managed by `render_cherry_import_files()` |
| global | `~/Library/Application Support/CherryStudio/mcp-import/managed/all.json` | generated | Aggregated MCP imports |

Install agent name: N/A (desktop app)
