# Claude Code Ecosystem Surface

## Sources

- Skills: https://docs.claude.com/en/docs/claude-code/skills
- Plugins: https://code.claude.com/docs/en/plugins
- Plugin marketplaces: https://code.claude.com/docs/en/plugin-marketplaces
- Hooks: https://code.claude.com/docs/en/hooks
- Extension overview: https://code.claude.com/docs/en/features-overview

## Extension surfaces

- `CLAUDE.md` persistent context.
- Skills under personal/project/plugin locations.
- Plugins bundling commands, agents, hooks, skills, MCP servers, LSP servers, monitors.
- Hooks triggered on permission/tool/session/task events.
- Subagents and agent teams.
- MCP servers.

## Planning implications

- Highest priority native projection target because it supports skills and plugins directly.
- Plugin marketplace manifest should be generated from canonical registry.
- Skill `allowed-tools` is Claude-specific/experimental and must not be assumed portable.
- Hooks are powerful but high risk; model as deterministic guardrails with tests.
