# Harness Compatibility Matrix

This matrix is a planning artifact. `validated` support must still be proven by conformance tests.

| Harness | Support tier | Native skills? | MCP? | Plugins/extensions? | Primary repo artifacts | Key caveat |
|---|---|---:|---:|---:|---|---|
| Claude Desktop | planned-research-backed | unknown | yes | unknown | mcp, instructions, plugin-adjacent | MCP/local connectors; plugin parity not fully assumed |
| Claude Code | validated-target | yes | yes | yes | skills, plugins, hooks, mcp, agents | Skills, plugins, hooks, subagents, MCP, settings scopes |
| ChatGPT | planned-research-backed | unknown | yes | yes | apps-sdk, actions, openapi, mcp-preview | Custom GPT Actions and Apps SDK/MCP preview; workspace developer mode constraints |
| Codex | repo-present-validation-required | fallback | yes | yes | agents-md, mcp, cli, sandbox | AGENTS.md, Codex CLI MCP, cloud sandbox tasks |
| GitHub Copilot Web / Cloud Agent | planned-research-backed | yes | yes/cloud-agent | unknown | skills, custom-agents, mcp, instructions | Agent skills, custom agents, repository MCP config, instructions, Agent HQ preview |
| GitHub Copilot CLI | planned-research-backed | yes | yes | unknown | skills, cli, agents, instructions | Skills, custom instructions, custom agents, /skills commands |
| OpenCode | repo-present-validation-required | yes | yes | yes | skills, agents, plugins, mcp, config | Native skill discovery across .opencode/.claude/.agents plus agents/plugins/MCP |
| Gemini CLI | repo-present-validation-required | fallback | yes | yes | extensions, gemini-md, mcp, custom-commands | Extensions package prompts, MCP servers, commands, context files |
| Google Antigravity | experimental | unknown | yes | unknown | rules, agents, browser, terminal, artifacts | Agent-first IDE with Editor/Manager, artifacts, editor/terminal/browser surfaces |
| Perplexity Desktop / Mac | experimental | unknown | yes | unknown | local-mcp, helper-app | Local MCP on macOS helper; remote MCP coming soon |
| Cherry Studio | planned-research-backed | unknown | yes | unknown | mcp, built-in-uv-bun, presets | MCP UI, built-in uv/bun, auto-install beta, presets |
| Cursor Editor | repo-present-validation-required | unknown | yes | rules/api | rules, mcp, background-agents | Rules, AGENTS/CLAUDE, MCP, background agents, environment.json |
| Cursor Agent CLI/Web | planned-research-backed | fallback | yes | rules/api | cli, mcp, web-agent, api | CLI JSON/text output, MCP manager, background/web/mobile/API |

## Support-tier rule

No README, docs page, or generated matrix may claim stronger support than the manifest tier.
