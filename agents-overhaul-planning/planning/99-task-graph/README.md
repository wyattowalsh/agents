---
status: planning
owner: platform-orchestrator
last_updated: 2026-05-01
principle: skills-first, specs-governed, mcp-when-live-state-required
---

# Subagent Task Graph

## Objective

Coordinate massively parallel execution across platform, skills, MCP, harness, docs, CI, security, UX, and OpenSpec teams.

## Team topology

| Team | Scope |
|---|---|
| Platform Core | schemas, registries, adapter contracts |
| OpenSpec Team | OpenSpec changes/specs/tasks/archive workflow |
| Skills Team | skills-first refactor, external skill curation, skill evals |
| MCP Team | MCP curation, promotion gates, smoke tests |
| Harness Adapter Teams | one team per harness |
| UX/CLI Team | doctor, sync preview, rollback, catalog browser |
| CI/Conformance Team | fixtures, clean-room installs, docs truth, release gates |
| Security/Supply Chain Team | provenance, secret safety, sandboxing, trust tiers |
| Docs & AI Instructions Team | README, AGENTS.md, generated docs, setup guides |

## Critical path

```text
CORE-001 -> CORE-002 -> CORE-003 -> CORE-004 -> OPS-001 -> OPS-002 -> OPS-003 -> CORE-005 -> CI-006 -> DOC-010
```

## Merge-conflict minimization

- Core schemas land before adapter updates.
- Each harness gets a separate PR lane.
- Docs generation contract lands before large docs rewrites.
- Skills, MCP, and plugin registries are separate files.
- README/AGENTS changes land after policy docs stabilize.

## Machine-readable graph

See `subagent-graph.json`.

## Maximal expansion

This bundle expands the graph to `482` total tasks and adds clusters `C10`–`C19` for progressive docs architecture, Agent Skills lifecycle, MCP audit/replacement, harness idiosyncrasies, plugin packaging, UI/UX productization, docs truth, security/provenance, evals/observability, and OpenSpec finalization.

See `subagent-task-definitions-expanded.md` for the newly added granular tasks.
