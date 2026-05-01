# Dispatch: agents-c03-mcp-audit

## Child OpenSpec Change

`agents-c03-mcp-audit`

## Mission

Normalize MCP inventory into a live-systems registry and identify static/redundant MCPs that should become skills instead.

## Allowed Files And Directories

- `mcp/`
- `mcp.json`
- `planning/35-mcp-audit/`
- `planning/manifests/`
- `openspec/changes/agents-c03-mcp-audit/`
- MCP smoke fixtures

## Forbidden Shared Files

- `skills/`
- `README.md`
- `AGENTS.md`

## Dependencies

- `agents-c01-registry-core`
- repo-sync inventory from `agents-c00-repo-sync`

## Expected Artifacts

- MCP registry records with transport, auth, secrets, sandbox, and smoke-fixture fields
- MCP risk matrix fragments
- skill-replacement recommendations

## Validation Commands

- `uv run wagents openspec validate`
- MCP registry schema validation
- MCP smoke fixture checks where safe

## Commit Requirement

Commit only this lane's changes with a conventional commit.

## Final Response Format

Return completed scope, files changed, validation commands/results, blockers, and commit hash.
