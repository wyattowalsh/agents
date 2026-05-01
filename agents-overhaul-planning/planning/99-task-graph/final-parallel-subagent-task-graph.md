# Final Parallel Subagent Task Graph

Generated: `2026-05-01T10:44:04.042207+00:00`

## Counts

- External repositories represented: 93.
- Added external repository tasks: 372.
- Final task count: 854.

## Added Clusters

| Cluster | Name | Purpose |
|---|---|---|
| C20 | External Repository Intake and Evaluation | Verify each user-provided repo before promotion. |
| C21 | Knowledge Graph and Context Memory Integration | Graphify/code graph/codebase-memory/context candidates. |
| C22 | Session Replay, Telemetry, and Agent Analytics | Session viewers, replay exporters, token/cost telemetry. |
| C23 | Skill Registry and Package Manager Ecosystem | Awesome lists, official skills, package managers. |
| C24 | External UX and Multi-Agent Control Plane Patterns | Kanban, desktop apps, terminals, control planes. |
| C25 | Security Quarantine and Provenance Review | Auth/proxy/offensive/security-sensitive assets. |

## Critical Path

1. Repo sync and OpenSpec reconciliation.
2. Registry schema freeze.
3. Support-tier and external-intake policy freeze.
4. Parallel external intake.
5. Security/license/provenance review.
6. Skill/MCP/plugin decision.
7. Conformance fixture.
8. Docs and AI-instruction sync.
9. OpenSpec archive readiness.

## Merge Conflict Strategy

- External intake tasks write only manifest rows, child OpenSpec fragments, or scoped docs.
- Global docs and README are updated only by the Docs team after manifests stabilize.
- `mcp.json` changes are postponed until MCP audit and replacement decisions are complete.
- `skills/` additions are postponed until skill conformance and provenance checks pass.
- Harness-specific teams work in isolated harness folders and fixture paths.
