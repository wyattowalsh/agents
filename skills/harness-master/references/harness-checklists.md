# Harness Checklists

## Contents

1. [Claude Code](#claude-code)
2. [Codex](#codex)
3. [Cursor](#cursor)
4. [Gemini CLI](#gemini-cli)
5. [Antigravity](#antigravity)
6. [GitHub Copilot](#github-copilot)
7. [OpenCode](#opencode)

## Claude Code

Check:

- `CLAUDE.md` vs `AGENTS.md` scope split
- `.claude/rules/**` coverage and overlap
- project/global settings placement
- local vs global overrides
- whether generated or merged config is being hand-edited instead of a canonical source

## Codex

Check:

- `AGENTS.md` clarity and scope
- `.codex/config.toml` presence and trust assumptions
- approval/sandbox behavior where configured
- MCP config hygiene if present in `config.toml`
- whether project config duplicates global config unnecessarily

## Cursor

Check:

- `AGENTS.md` vs `.cursor/rules/**` responsibilities
- nested `AGENTS.md` opportunities or conflicts
- `.cursor/mcp.json` location and interpolation quality
- `~/.cursor/permissions.json` fit for the repo's risk profile
- whether UI-only user/team rules are creating blind spots that must be called out

## Gemini CLI

Check:

- `GEMINI.md` quality and wrapper behavior
- `.gemini/settings.json` necessity vs noise
- project vs global settings split
- whether the repo relies on generated wrapper content that should instead be changed at a canonical source

## Antigravity

Check:

- `~/.gemini/antigravity/mcp_config.json` structure and auth configuration
- `command` vs `serverUrl` usage
- `headers`, OAuth, and disabled tool handling
- settings and approval behavior where observable
- worktree support assumptions
- project-level compatibility with repo wrapper files, clearly labeled as `repo-observed` if not first-party verified

## GitHub Copilot

Check:

- `.github/copilot-instructions.md` freshness and generated-file status
- `.github/instructions/**` and `.github/hooks/**` coherence
- `.vscode/mcp.json` quality and project fit
- global settings placement in `~/.copilot/settings.json`, subagent caps in `~/.config/copilot-subagents.env`, and MCP paths
- whether built-in GitHub MCP is being duplicated unnecessarily

## OpenCode

Check:

- `AGENTS.md` vs `opencode.json` split of responsibilities
- `instructions` list correctness
- `skills.paths` correctness and portability
- repo-native `.opencode/agents/**` usage
- global OpenCode skill-dir coverage and whether missing skill discovery is a real issue
- global plugin files in `~/.config/opencode/plugins/` (e.g., `approval-notify.ts`) and whether they are up to date with repo-managed sources
- any global OpenCode rules or rule-like surfaces that remain blind spots in the current session
- whether repo-observed companion files such as `.opencode/ocx.jsonc` are relevant or accidental

## Cherry Studio

Check:

- MCP import files freshness (`mcp-import/managed/`)
- Whether generated MCP files match current registry
- App settings alignment with repo policy
