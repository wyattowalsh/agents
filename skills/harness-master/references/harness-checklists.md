# Harness Checklists

## Contents

1. [Claude Code](#claude-code)
2. [Claude Desktop](#claude-desktop)
3. [ChatGPT](#chatgpt)
4. [Codex](#codex)
5. [GitHub Copilot Web](#github-copilot-web)
6. [GitHub Copilot CLI](#github-copilot-cli)
7. [Cursor](#cursor)
8. [Gemini CLI](#gemini-cli)
9. [Antigravity](#antigravity)
10. [OpenCode](#opencode)
11. [Perplexity Desktop](#perplexity-desktop)
12. [Cherry Studio](#cherry-studio)

## Claude Code

Check:

- `CLAUDE.md` vs `AGENTS.md` scope split
- `.claude/rules/**` coverage and overlap
- `.mcp.json` and `~/.claude.json` MCP/config placement
- project/global settings placement
- local vs global overrides
- whether generated or merged config is being hand-edited instead of a canonical source

## Claude Desktop

Check:

- `claude_desktop_config.json` validity and `mcpServers` shape
- whether desktop MCP config is incorrectly treated as Claude Code project state
- merged-file boundaries before proposing edits
- local command paths, environment fields, and security exposure

## ChatGPT

Check:

- `~/Library/Application Support/ChatGPT/mcp.json` only as repo-observed unless first-party docs verify it
- Apps SDK/Connectors docs for HTTPS `/mcp` endpoint expectations
- connector UI blind spots and developer-mode assumptions
- whether recommendations clearly separate local desktop MCP from web connector configuration

## Codex

Check:

- `AGENTS.md` clarity and scope
- `.codex/config.toml` presence and trust assumptions
- approval/sandbox behavior where configured
- MCP config hygiene if present in `config.toml`
- whether project config duplicates global config unnecessarily

## GitHub Copilot Web

Check:

- `.github/copilot-instructions.md` freshness and generated-file status
- `.github/instructions/**` and `.github/hooks/**` coherence
- `.vscode/mcp.json` quality and project fit
- Copilot coding agent, repository, and organization settings as blind spots when not locally observable
- whether built-in GitHub MCP is being duplicated unnecessarily

## GitHub Copilot CLI

Check:

- `~/.copilot/settings.json` trusted folders and permissions
- `~/.copilot/mcp-config.json` and alternate MCP config path
- `~/.config/copilot-subagents.env` caps if subagent fan-out is in scope
- CLI flags or local permissions that may bypass intended policy
- overlap with project `.vscode/mcp.json` and web/coding-agent surfaces

## Cursor

Check:

- `AGENTS.md` vs `.cursor/rules/**` responsibilities
- nested `AGENTS.md` opportunities or conflicts
- `.cursor/mcp.json` location and interpolation quality
- `.cursor/skills/**`, `.agents/skills/**`, `.cursor/agents/**`, and compatibility directory duplication
- `.cursor/hooks.json` and `~/.cursor/hooks.json` precedence
- `.cursor/cli.json` vs `~/.cursor/cli-config.json` permissions split
- `.cursorignore` coverage for sensitive or noisy paths
- `~/.cursor/permissions.json` fit for the repo's risk profile, with medium confidence if docs conflict
- UI-only user/team rules and Cloud Agent settings/secrets/API state as blind spots

## Gemini CLI

Check:

- `GEMINI.md` quality and wrapper behavior
- `.gemini/settings.json` necessity vs noise
- project vs global settings split
- `mcpServers` and `hooks` shape in settings files
- whether the repo relies on generated wrapper content that should instead be changed at a canonical source

## Antigravity

Check:

- `~/.gemini/antigravity/mcp_config.json` structure and auth configuration
- `command` vs `serverUrl` usage
- `headers`, OAuth, and disabled tool handling
- OAuth token file presence/permissions only; never read token values
- settings and approval behavior where observable
- terminal auto-execution and non-workspace file access policy
- worktree support assumptions
- project-level compatibility with repo wrapper files, clearly labeled as `repo-observed` if not first-party verified

## OpenCode

Check:

- `AGENTS.md` vs `opencode.json` split of responsibilities
- `instructions` list correctness
- `skills.paths` correctness and portability
- repo-native `.opencode/agents/**` usage
- global OpenCode skill-dir coverage and whether missing skill discovery is a real issue
- global plugin files in `~/.config/opencode/plugins/` and whether they are up to date with repo-managed sources
- any global OpenCode rules or rule-like surfaces that remain blind spots in the current session
- whether repo-observed companion files such as `.opencode/ocx.jsonc` are relevant or accidental

## Perplexity Desktop

Check:

- Perplexity Mac app local MCP connector UI as a blind spot
- `.perplexity/skills/*.md` and `~/.perplexity/skills/*.md` only as repo-observed unless first-party docs verify filesystem loading
- whether generated/synced skill files have drifted from repo source
- whether the request is really about Perplexity Desktop MCP, Perplexity Computer Skills, or both
- confidence downgrade in any recommendation that depends on UI-only connector state

## Cherry Studio

Check:

- MCP import files freshness (`mcp-import/managed/*.json`)
- whether generated MCP files match current registry
- App settings alignment with repo policy
- `.cherry/presets/*.json` and global `presets/*.json` sync drift
- `mcpServers` wrapper shape, transport type, URL/baseUrl handling, and single-server vs JSON-edit import behavior
