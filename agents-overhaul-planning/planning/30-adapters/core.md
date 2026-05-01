---
status: planning
owner: platform-orchestrator
last_updated: 2026-05-01
principle: skills-first, specs-governed, mcp-when-live-state-required
---

# Core Adapter Contracts

## Responsibilities

- load canonical registries
- validate schemas
- detect harness installation/config paths
- render desired state
- produce diff
- apply transaction
- rollback transaction
- emit observability events

## Acceptance criteria

- No adapter writes directly without transaction wrapper.
- Every adapter has golden input/output fixtures.
- Every adapter exposes unsupported-field warnings.
