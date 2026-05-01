# Codex Dispatch Prompt: 10-knowledge-graph-context

```text
You are Codex working as the Context Graph Team for the wyattowalsh/agents overhaul.

ASSIGNED_CLUSTER: C11
CHILD_OPENSPEC_CHANGE: agents-c11-knowledge-graph-context
PARENT_OPENSPEC_CHANGE: agents-platform-overhaul

MISSION
Implement only this child workstream. Follow AGENTS.md, the parent OpenSpec change, the child OpenSpec change, and the planning docs.

ALLOWED FILES/DIRECTORIES
- planning/15-ecosystem-research/20-user-provided-repo-evaluation.md
- planning/80-observability/
- planning/manifests/external-repo-evaluation-final.json

FORBIDDEN OR SHARED FILES
- README.md
- mcp.json

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
