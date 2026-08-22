# Harness Surfaces

## Contents

1. [Legend](#legend)
2. [Claude Code](#claude-code)
3. [Claude Desktop](#claude-desktop)
4. [ChatGPT](#chatgpt)
5. [Codex](#codex)
6. [Cursor](#cursor)
7. [Cursor Agent CLI](#cursor-agent-cli)
8. [Grok Build](#grok-build)
9. [OpenCode](#opencode)
10. [Perplexity Desktop](#perplexity-desktop)
11. [Cherry Studio](#cherry-studio)

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

Editor, desktop, web, and Cloud Agent aliases (`cursor`, `cursor-editor`, `cursor-desktop`, `cursor-web`, `cursor-cloud`, `cursor-cloud-agent`, `cursor-background-agent`) stay on this harness. Cursor Agent CLI is a separate canonical harness: [Cursor Agent CLI](#cursor-agent-cli).

Shared SSOT with the CLI (rendered once by the Cursor adapter, `harness="cursor"`): `.cursor/hooks.json`, `.cursor/mcp.json`, `.cursor/skills`, `.cursor/agents`, and the matching `~/.cursor/{hooks,mcp,skills,agents}` trees. CLI-only permissions live under `cursor-cli`.

| Scope | Surface | Role | Notes |
|-------|---------|------|-------|
| project | `AGENTS.md` | authoritative or secondary | Simple instruction path; compare with `.cursor/rules/**` |
| project | nested `AGENTS.md` | secondary | More specific directory-scoped instructions |
| project | `.cursor/rules/*.md` / `.cursor/rules/*.mdc` | authoritative when present | Project rules system |
| project | `.cursor/mcp.json` | authoritative when present | Shared project MCP config (same file as CLI) |
| project | `.cursor/skills/**/SKILL.md` | authoritative when present | Cursor-native project skills; shared with CLI |
| project | `.agents/skills/**/SKILL.md` | secondary | Compatibility skills directory |
| project | `.cursor/agents/*.md` | authoritative when present | Cursor subagents; shared with CLI |
| project | `.cursor/hooks.json` | authoritative when present | Shared project hooks; cloud agents may also run repo hooks. Fleet-only — no Plannotator (home `~/.cursor/hooks.json` only) |
| project | `.cursorignore` | authoritative when present | Files excluded from Cursor context |
| global | `~/.cursor/mcp.json` | authoritative | Shared global MCP config |
| global | `~/.cursor/permissions.json` | authoritative, medium confidence | Still referenced by current docs; CLI permissions are in `cli.json` / `cli-config.json` |
| global | `~/.cursor/hooks.json` | authoritative when present | Shared user hooks; home-only Plannotator `CreatePlan`/`SwitchMode` when synced |
| global | `~/.cursor/skills` | authoritative when present | Cursor-native global skills — durable synced surface for `wagents skills sync` |
| global | `~/.agents/skills` | secondary | Compatibility / Skills CLI universal store; store presence alone is **not** durable Cursor sync |
| global | `~/.cursor/agents/*.md` | authoritative when present | Global Cursor subagents; shared with CLI |
| global | Cursor user rules in settings UI | blind-spot | UI-managed unless exported |
| global | Team rules/dashboard | blind-spot | Org-managed, not observable from local files |
| global | Cloud Agent settings/secrets/API state | blind-spot | Dashboard/API-managed web surfaces |
| global | Team/Enterprise hooks | blind-spot | Admin-distributed hooks may not be local files |

Install agent name: `cursor`

## Cursor Agent CLI

Canonical id `cursor-cli`. Binary: `agent` (also `cursor-agent`). Aliases `cursor-cli`, `cursor-agent`, `cursor-agent-cli`, `agent-cli`, and `agent` normalize here. Review this harness independently; do not collapse it into an editor-only `cursor` report.

Official CLI docs confirm the CLI loads `AGENTS.md`, `CLAUDE.md`, `.cursor/rules`, shared `mcp.json` / skills / hooks, project `.cursor/cli.json` permissions, and remaining settings in user-owned `~/.cursor/cli-config.json`. Shared hooks/MCP/skills/agents stay one SSOT owned by the Cursor adapter. `cursor-cli` is a consumer, not a second render target. ACP stays the `cursor-acp` row (`agent acp`); `agent worker` is out of repo sync.

| Scope | Surface | Role | Notes |
|-------|---------|------|-------|
| project | `AGENTS.md` | authoritative | CLI applies root `AGENTS.md` as rules |
| project | `CLAUDE.md` | secondary | Official CLI also applies root `CLAUDE.md` as rules |
| project | `instructions/cursor-cli-global.md` | authoritative when present | CLI-specific overlay; thin `.cursor/rules/cursor-cli.mdc` pointer |
| project | `.cursor/rules/*.md` / `.cursor/rules/*.mdc` | authoritative when present | Shared rules, including the CLI overlay pointer |
| project | `.cursor/mcp.json` | authoritative when present | Shared project MCP; CLI auto-detects the same file as the editor |
| project | `.cursor/skills/**/SKILL.md` | authoritative when present | Shared Cursor-native project skills |
| project | `.agents/skills/**/SKILL.md` | secondary | Compatibility skills directory |
| project | `.cursor/agents/*.md` | authoritative when present | Shared project subagents |
| project | `.cursor/hooks.json` | authoritative when present | Shared project hooks plus plugin hooks; fleet-only (no Plannotator). Do not add `cursor-cli` to hook-registry render lists |
| project | `.cursor/cli.json` | authoritative when present | CLI-only project permissions (`permissions.allow` / `permissions.deny`). Official docs: only permissions may be project-scoped |
| project | `.cursor/worktrees.json` | authoritative when present | Worktree setup for `agent --worktree`; this repo does not author the file by default |
| project | `plugin.json` | repo-observed | Portable Agent Plugins 1.0 manifest. CLI may load plugins via `--plugin-dir` or marketplace; do not infer auto-install |
| project | `wagents/cursor_cli_doctor.py` | repo-observed | Read-only doctor backing `wagents cursor-cli doctor` |
| project | `config/cursor-global-hooks.json` | repo-observed | Cursor Plannotator home template (`CreatePlan` / `SwitchMode`); not rendered into project hooks |
| global | `~/.cursor/hooks/plannotator-plan-hook.py` | authoritative when present | Home-copied fail-open shim; `wagents cursor-cli plannotator sync` |
| global | `~/.cursor/mcp.json` | authoritative | Shared global MCP |
| global | `~/.cursor/cli-config.json` | authoritative | User-owned global CLI config. Sync SHALL NOT write it or `state.vscdb`. Usage review: key presence only |
| global | `~/.cursor/hooks.json` | authoritative when present | Shared user hooks; home-only Plannotator `CreatePlan`/`SwitchMode` when synced |
| global | `~/.cursor/skills` | authoritative when present | Shared Cursor-native global skills; Skills CLI adapter remains `cursor` |
| global | `~/.agents/skills` | secondary | Compatibility / Skills CLI universal store |
| global | `~/.cursor/agents/*.md` | authoritative when present | Shared global subagents |
| global | `~/.cursor/settings.json` | authoritative when present | User plugin enablement (`enabled_plugins`); marketplace add is operator-opt-in |
| global | CLI plugin marketplace auth | blind-spot | `agent plugin marketplace add/list` may require account auth and is not repo-synced |
| global | Team/enterprise hooks | blind-spot | Admin-distributed hooks may load outside local `hooks.json` |
| global | Dashboard MCP and worker pools | blind-spot | Team MCP, Cloud Agent handoff, and `agent worker` pools are dashboard-managed |
| global | `cli-config.json` values | blind-spot | Report key presence only; do not print secret or account values |

Install agent name: `cursor` (Skills CLI adapter stays `cursor`; do not recommend `-a cursor-cli`)

## Grok Build

| Scope | Surface | Role | Notes |
|-------|---------|------|-------|
| project | `plugin.json` + `skills/*/SKILL.md` | authoritative when configured | A normalized `~/.grok/config.toml` plugin path resolving to this valid repo root is the preferred non-CLI owner for repo skills |
| project | `.grok/workflows/*.rhai` | authoritative source when explicitly repo-owned | Saved-workflow source; project files are not a substitute for the user workflow projection |
| global | `~/.grok/config.toml` `[plugins].paths` | authoritative | Config-path plugin ownership; resolve tilde, relative paths, and symlinks before comparing roots |
| global | `~/.grok/workflows/*.rhai` | authoritative | User saved-workflow discovery root; project canonical workflows require separate receipt-bound projection |
| global | `~/.agents/skills`, `~/.claude/skills`, `~/.grok/skills` | secondary/collision roots | For plugin-covered repo skills these are duplicate exposures; curated external skills retain Claude-alias-plus-mirror behavior |
| project | `config/grok-plannotator-hooks.json` | repo-observed | Canonical policy for Plannotator plan-mode hooks (PreToolUse for enter/exit); rendered on sync to global hooks dir |
| global | `~/.grok/hooks/*.json` | authoritative | Grok hook surfaces (directory of JSON hook files); includes plannotator.json when synced via repo Grok plannotator install |
| global | `~/.grok/hooks/plannotator.json` | authoritative (when present) | Rendered Plannotator hooks (exit_plan_mode -> block/deny shim + context improvement) |

Grok Build also observes shared `AGENTS.md` / `instructions/grok-global.md` and MCP via the common sync pipeline (see harness-surface-registry for other projection surfaces). Config-path plugin ownership and Skills CLI ownership are distinct evidence classes: a valid configured plugin can cover only repo skills whose readable portable `SKILL.md` frontmatter has a matching directory/name and non-empty description, without a copy in any global skill directory. Invalid or uncovered skills retain their fallback owner. A saved workflow still requires its own user projection.

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
