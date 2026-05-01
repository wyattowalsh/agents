# Cursor Editor and Cursor Agent Ecosystem Surface

## Sources

- CLI overview: https://docs.cursor.com/en/cli
- CLI usage: https://docs.cursor.com/en/cli/using
- CLI MCP: https://docs.cursor.com/cli/mcp
- MCP overview: https://docs.cursor.com/advanced/model-context-protocol
- Background agents: https://docs.cursor.com/en/background-agents
- Background agents API: https://docs.cursor.com/background-agent/api/overview

## Extension surfaces

- `.cursor/rules`.
- `AGENTS.md` and `CLAUDE.md` loaded by CLI as rules.
- MCP config shared between editor and CLI.
- `cursor-agent` interactive and print/non-interactive modes.
- JSON/text output in non-interactive mode.
- Background agents with `.cursor/environment.json`, GitHub connection, encrypted secrets, remote Ubuntu machine.
- Web/mobile agents and API.

## Planning implications

- Add JSON-output conformance tests for `cursor-agent` automation flows.
- Treat background agent API as beta; do not rely on it for core install path.
- Add environment.json docs if repo supports Cursor remote/background agent bootstrap.
- Strong candidate for dashboard-like async workflow patterns.
