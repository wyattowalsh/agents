# Latest Doc Sources

## Contents

1. [Lookup Order](#lookup-order)
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

## Lookup Order

For any "latest" or "official" claim, use this order:

1. `llms.txt` or an official docs index if available
2. first-party docs pages for the harness feature being reviewed
3. canonical vendor repo docs if first-party docs are incomplete
4. repository-observed sync logic for local conventions not covered by vendor docs
5. general web fallback only if the above are unavailable

Always record which source was used.

## Claude Code

Preferred sources:

- `https://code.claude.com/docs/llms.txt`
- `https://code.claude.com/docs/en/settings.md`
- `https://code.claude.com/docs/en/memory.md`
- `https://code.claude.com/docs/en/claude-directory.md`
- `https://code.claude.com/docs/en/mcp.md`
- `https://code.claude.com/docs/en/skills.md`

Use for:

- `CLAUDE.md` / memory behavior
- settings scope and precedence
- `.mcp.json` and `~/.claude.json` MCP/config behavior
- skills and `.claude` directory conventions

## Claude Desktop

Preferred sources:

- `https://modelcontextprotocol.io/docs/develop/connect-local-servers.md`
- `https://modelcontextprotocol.io/llms-full.txt`
- `https://support.anthropic.com/` only if product-specific Desktop behavior is needed

Use for:

- `~/Library/Application Support/Claude/claude_desktop_config.json`
- local MCP server JSON shape
- desktop-app-only behavior distinct from Claude Code

## ChatGPT

Preferred sources:

- `https://developers.openai.com/apps-sdk/llms.txt`
- `https://developers.openai.com/apps-sdk/deploy/connect-chatgpt.md`
- `https://developers.openai.com/apps-sdk/build/examples.md`
- repository evidence for `~/Library/Application Support/ChatGPT/mcp.json`

Use for:

- ChatGPT Apps and Connectors flow
- HTTPS `/mcp` endpoint expectations
- local desktop MCP config only when explicitly tagged `repo-observed`

Do not claim `~/Library/Application Support/ChatGPT/mcp.json` is first-party documented unless current docs prove it.

## Codex

Preferred sources:

- `https://developers.openai.com/codex/llms.txt`
- `https://developers.openai.com/codex/llms-full.txt`
- `https://developers.openai.com/codex/config-basic`
- `https://developers.openai.com/codex/config-reference`
- `https://developers.openai.com/codex/guides/agents-md`

Use for:

- `AGENTS.md` behavior
- `config.toml` precedence and defaults
- approval, sandbox, app, CLI, plugin, and MCP config conventions

## GitHub Copilot Web

Preferred sources:

- `https://docs.github.com/en/copilot`
- `https://docs.github.com/en/copilot/customizing-copilot/adding-repository-custom-instructions-for-github-copilot`
- `https://docs.github.com/en/copilot/concepts/coding-agent/coding-agent`
- `https://docs.github.com/en/copilot/how-tos/agents/copilot-coding-agent/extending-copilot-coding-agent-with-the-model-context-protocol-mcp`

Use for:

- GitHub.com instructions and repository customization
- Copilot coding agent/cloud behavior
- repository/org settings and cloud-managed blind spots

## GitHub Copilot CLI

Preferred sources:

- `https://docs.github.com/en/copilot/how-tos/copilot-cli/set-up-copilot-cli/configure-copilot-cli`
- `https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-mcp-servers`
- `https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/customize-copilot-cli`

Use for:

- `~/.copilot/settings.json`
- `~/.copilot/mcp-config.json`
- CLI permissions, trusted folders, URL/path/tool allowlists
- native GitHub MCP behavior

## Cursor

Preferred sources:

- `https://cursor.com/llms.txt`
- `https://cursor.com/docs/rules.md`
- `https://cursor.com/docs/mcp.md`
- `https://cursor.com/docs/agent/overview.md`
- `https://cursor.com/docs/agent/security.md`
- `https://cursor.com/docs/skills.md`
- `https://cursor.com/docs/subagents.md`
- `https://cursor.com/docs/hooks.md`
- `https://cursor.com/docs/cli/overview.md`
- `https://cursor.com/docs/cli/reference/configuration.md`
- `https://cursor.com/docs/cli/reference/permissions.md`
- `https://cursor.com/docs/cloud-agent`

Use for:

- `AGENTS.md` vs `.cursor/rules/**`
- nested `AGENTS.md` support
- `.cursor/mcp.json` project/global behavior
- skills, subagents, hooks, CLI config, cloud agents, and `.cursorignore`
- `~/.cursor/permissions.json` only with medium confidence if docs remain inconsistent

## Gemini CLI

Preferred sources:

- `https://geminicli.com/docs/reference/configuration/`
- `https://geminicli.com/docs/cli/gemini-md/`
- `https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/cli/tutorials/mcp-setup.md`
- `https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/hooks/reference.md`

Use for:

- `GEMINI.md` behavior
- settings precedence
- project vs user settings placement
- `mcpServers` and hooks in settings files

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
- auth, OAuth, and token-file presence checks
- settings, approval behavior, and non-workspace file access policy
- notable limits such as worktree support and third-party software restrictions

Treat project-native Antigravity file behavior as lower-confidence unless the current session retrieves direct first-party evidence for it.

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

## Perplexity Desktop

Preferred sources:

- `https://www.perplexity.ai/help-center/en/articles/11502712-local-and-remote-mcps-for-perplexity`
- `https://www.perplexity.ai/help-center/en/articles/13914413-how-to-use-computer-skills`
- repository evidence for `.perplexity/skills` and `~/.perplexity/skills`

Use for:

- Perplexity Mac app local MCP connector UI
- Computer Skills behavior
- repo-observed skill-file sync, with explicit degraded confidence

Do not claim official filesystem loading for `.perplexity/skills` unless current first-party docs prove it.

## Cherry Studio

Preferred sources:

- `https://docs.cherry-ai.com/docs/en-us/advanced-basic/mcp/config`
- `https://docs.cherry-ai.com/docs/en-us/advanced-basic/mcp/install`
- `https://raw.githubusercontent.com/CherryHQ/cherry-studio/main/src/renderer/src/types/mcp.ts`
- `https://raw.githubusercontent.com/CherryHQ/cherry-studio/main/src/renderer/src/pages/settings/MCPSettings/AddMcpServerModal.tsx`
- `https://raw.githubusercontent.com/CherryHQ/cherry-studio/main/src/renderer/src/pages/settings/MCPSettings/EditMcpJsonPopup.tsx`

Use for:

- Cherry Studio MCP JSON shape and transports
- `mcpServers` import/edit behavior
- bundled `uv`/`bun` runtime paths
- repo-observed presets and generated import files
