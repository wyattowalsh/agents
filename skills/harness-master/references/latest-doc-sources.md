# Latest Doc Sources

## Contents

1. [Lookup Order](#lookup-order)
2. [Claude Code](#claude-code)
3. [Codex](#codex)
4. [Cursor](#cursor)
5. [Gemini CLI](#gemini-cli)
6. [Antigravity](#antigravity)
7. [GitHub Copilot](#github-copilot)
8. [OpenCode](#opencode)

## Lookup Order

For any “latest” or “official” claim, use this order:

1. `llms.txt` or an official docs index if available
2. first-party docs pages for the harness feature being reviewed
3. canonical vendor repo docs if first-party docs are incomplete
4. general web fallback only if the above are unavailable

Always record which source was used.

## Claude Code

Preferred sources:

- `https://code.claude.com/docs/llms.txt`
- `https://code.claude.com/docs/en/settings.md`
- `https://code.claude.com/docs/en/memory.md`
- `https://code.claude.com/docs/en/claude-directory.md`
- `https://code.claude.com/docs/en/skills.md`

Use for:

- `CLAUDE.md` / memory behavior
- settings scope and precedence
- skills and `.claude` directory conventions
- MCP/config adjacency questions when docs cover them

## Codex

Preferred sources:

- `https://developers.openai.com/codex/config-basic`
- `https://developers.openai.com/codex/config-reference`
- `https://developers.openai.com/codex/guides/agents-md`

Use for:

- `AGENTS.md` behavior
- `config.toml` precedence and defaults
- approval, sandbox, and MCP config conventions

## Cursor

Preferred sources:

- `https://cursor.com/llms.txt`
- `https://cursor.com/docs/rules`
- `https://cursor.com/docs/mcp`
- `https://cursor.com/docs/reference/permissions`

Use for:

- `AGENTS.md` vs `.cursor/rules/**`
- nested `AGENTS.md` support
- `.cursor/mcp.json` project/global behavior
- `~/.cursor/permissions.json` and allowlists

## Gemini CLI

Preferred sources:

- `https://geminicli.com/docs/reference/configuration/`
- `https://geminicli.com/docs/cli/gemini-md/`

Use for:

- `GEMINI.md` behavior
- settings precedence
- project vs user settings placement

If first-party docs are hard to fetch, prefer the canonical Gemini CLI repo docs before general web fallback.

## Antigravity

Preferred sources:

- `https://antigravity.google/docs/mcp`
- `https://antigravity.google/docs/settings`
- `https://antigravity.google/docs/agent-modes-settings`
- `https://antigravity.google/docs/faq`

Use for:

- MCP integration and config structure
- `~/.gemini/antigravity/mcp_config.json`
- auth and OAuth flows
- settings and approval behavior
- notable limits such as worktree support and third-party software restrictions

Treat project-native Antigravity file behavior as lower-confidence unless the current session retrieves direct first-party evidence for it.

## GitHub Copilot

Preferred sources:

- `https://docs.github.com/en/copilot/how-tos/copilot-cli/set-up-copilot-cli/configure-copilot-cli`
- `https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-mcp-servers`

Use for:

- project instructions vs global instructions
- MCP config paths and server definitions
- native GitHub MCP behavior

If multiple Copilot docs overlap, prefer the doc that explicitly covers CLI/customization or MCP configuration.

## OpenCode

Preferred sources:

- `https://dev.opencode.ai/docs/config/`
- `https://dev.opencode.ai/docs/rules`
- `https://dev.opencode.ai/docs/skills/`

Use for:

- `opencode.json` structure
- `instructions` loading
- `skills.paths`
- OpenCode-native rules/skills/agents behavior

If first-party docs and repo-observed behavior diverge, report the contradiction explicitly.
