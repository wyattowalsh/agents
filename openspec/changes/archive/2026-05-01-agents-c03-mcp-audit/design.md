# Design

## Decision

Complete the MCP audit lane as a registry-grounded classification contract. The lane defines inventory fields, live-state necessity, replacement candidates, risk matrix fields, smoke fixture requirements, and secret-handling boundaries.

## Rationale

MCP servers are appropriate when live state is required. Static docs, deterministic repo-local transformations, and duplicate capabilities should move toward skills or CLI fixtures. This split reduces credential and live-mutation risk without changing current MCP config during a dirty worktree.

## Implementation Notes

- `planning/35-mcp-audit/00-mcp-audit-control-plane.md` is the lane-owned contract.
- Secret paths are described by class and path pattern only; values are never read.
- Future registry edits should happen only with C01/C06 coordination.

## Risks

- `mcp.json` and registry files may be dirty from unrelated work, so this pass avoids modifying them.
- Some MCP smoke fixtures require real credentials and must remain opt-in.
