# Dispatch: agents-c15-security-quarantine

## Child OpenSpec Change

`agents-c15-security-quarantine`

## Mission

Quarantine auth-bridging, proxying, credential-sharing, offensive-security, and provenance-sensitive external assets.

## Allowed Files And Directories

- `planning/50-config-safety/`
- `planning/15-ecosystem-research/`
- `planning/manifests/`
- `openspec/changes/agents-c15-security-quarantine/`

## Forbidden Shared Files

- `skills/`
- `mcp/`
- `mcp.json`
- `README.md`
- `AGENTS.md`

## Dependencies

- `agents-c10-external-repo-intake`

## Expected Artifacts

- quarantine register
- exception workflow
- threat-review checklist
- provenance requirements

## Validation Commands

- `uv run wagents openspec validate`
- policy/schema validation where implemented

## Commit Requirement

Commit only this lane's changes with a conventional commit.

## Final Response Format

Return completed scope, files changed, validation commands/results, blockers, and commit hash.
