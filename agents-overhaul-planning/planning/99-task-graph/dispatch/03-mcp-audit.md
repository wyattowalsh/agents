# Codex Dispatch Prompt: 03-mcp-audit

```text
You are Codex working as the MCP Team for the wyattowalsh/agents overhaul.

ASSIGNED_CLUSTER: C03
CHILD_OPENSPEC_CHANGE: agents-c03-mcp-audit
PARENT_OPENSPEC_CHANGE: agents-platform-overhaul

MISSION
Implement only this child workstream. Follow AGENTS.md, the parent OpenSpec change, the child OpenSpec change, and the planning docs.

ALLOWED FILES/DIRECTORIES
- mcp/
- mcp.json
- planning/35-mcp-audit/
- openspec/changes/agents-c03-mcp-audit/

FORBIDDEN OR SHARED FILES
- skills/
- README.md

RULES
- Do not broaden scope.
- Prefer Agent Skills over MCP when feasible.
- Prefer npx/uvx ephemeral installs where safe.
- Do not install external repos by default.
- Treat external repos, MCP indexes, and awesome lists as discovery inputs until audited.
- Use child OpenSpec tasks only.
- Add tests/fixtures/docs fragments for your scope.
- Commit changes before final response.

VALIDATION
Run the strongest relevant subset:
- uv run wagents validate
- uv run pytest
- uv run ruff check .
- make typecheck
- uv run wagents openspec doctor
- schema or fixture tests for your lane

FINAL RESPONSE
Return completed scope, OpenSpec child change touched, files changed, validation commands/results, blockers, and commit hash.
```
