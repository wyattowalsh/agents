# Harness Checklists

## Contents

1. [Claude Code](#claude-code)
2. [Claude Desktop](#claude-desktop)
3. [ChatGPT](#chatgpt)
4. [Codex](#codex)
5. [Cursor](#cursor)
6. [Grok Build](#grok-build)
7. [OpenCode](#opencode)
8. [Perplexity Desktop](#perplexity-desktop)
9. [Cherry Studio](#cherry-studio)

## Claude Code

Check:

- `CLAUDE.md` vs `AGENTS.md` scope split
- `.claude/rules/**` coverage and overlap
- `.mcp.json` and `~/.claude.json` MCP/config placement
- project/global settings placement
- local vs global overrides
- embedded hooks inside `.claude/settings*.json` (discover now emits explicit `kind: hooks` surfaces for settings files containing hooks)
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

## Grok Build

Check:

- `config/grok-plannotator-hooks.json` as source of truth for plannotator hooks policy (repo-observed)
- `~/.grok/hooks/*.json` (and specifically plannotator.json) after repo Grok plannotator install (`--hooks`) or stack sync
- that hooks changes are followed by "Restart Grok Build" (as documented)
- exit-plan-mode / enter-plan-mode hook shims and the plannotator-exit-plan-hook mapping
- presence of `kind: hooks` surfaces (global + project) when running harness-master discover / gap scans for grok-build
- whether plannotator hooks are unintentionally enabled/disabled via sync context

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
