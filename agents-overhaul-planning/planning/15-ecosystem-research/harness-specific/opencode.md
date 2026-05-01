# OpenCode Ecosystem Surface

## Sources

- Skills: https://opencode.ai/docs/skills
- MCP: https://opencode.ai/docs/mcp-servers
- Config: https://opencode.ai/docs/config/

## Extension surfaces

- Native skill discovery from `.opencode/skills`, `~/.config/opencode/skills`, `.claude/skills`, `~/.claude/skills`, `.agents/skills`, `~/.agents/skills`.
- Agents, plugins, MCP servers, and config scopes.
- Native `skill` tool loads skill body on demand.

## Planning implications

- OpenCode is a top-tier skills-first harness because it supports `.agents/skills` and `.claude/skills` compatibility.
- Avoid duplicating skill packages into multiple locations unless projection tests require it.
