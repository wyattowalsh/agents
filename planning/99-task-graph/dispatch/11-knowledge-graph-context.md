# Dispatch: agents-c11-knowledge-graph-context

## Child OpenSpec Change

`agents-c11-knowledge-graph-context`

## Mission

Evaluate knowledge graph and context-memory patterns as skills-first capabilities with optional live MCP query support only if justified.

## Allowed Files And Directories

- `planning/10-architecture/`
- `planning/15-ecosystem-research/`
- `planning/manifests/`
- `openspec/changes/agents-c11-knowledge-graph-context/`
- lane-specific fixtures

## Forbidden Shared Files

- `README.md`
- `AGENTS.md`
- `mcp.json`
- `skills/` unless explicitly assigned by skills lifecycle lane

## Dependencies

- `agents-c10-external-repo-intake`
- `agents-c13-skill-registry-intake`

## Expected Artifacts

- graph/context capability assessment
- skill-vs-MCP recommendation
- conformance fixture requirements

## Validation Commands

- `uv run wagents openspec validate`
- lane fixture validation when implemented

## Commit Requirement

Commit only this lane's changes with a conventional commit.

## Final Response Format

Return completed scope, files changed, validation commands/results, blockers, and commit hash.
