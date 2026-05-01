---
status: planning
owner: platform-orchestrator
last_updated: 2026-05-01
principle: skills-first, specs-governed, mcp-when-live-state-required
---

# Architecture Overview

## Target architecture

```mermaid
flowchart TD
  OS[OpenSpec specs and changes] --> REG[Canonical registry]
  INS[Canonical instructions] --> REG
  SK[Skills catalog] --> REG
  PL[Plugin catalog] --> REG
  MCP[MCP catalog] --> REG
  REG --> AD[Harness adapters]
  AD --> HC[Harness configs]
  REG --> DOC[Generated docs]
  REG --> CI[Conformance tests]
  CI --> REL[Release gates]
  UX[wagents CLI and dashboard] --> REG
  UX --> AD
```

## Core abstractions

1. `Capability`: a thing the repo can expose: instruction, skill, plugin, MCP, agent, hook, OpenSpec workflow.
2. `Harness`: an AI client/runtime with config paths and supported capability types.
3. `Projection`: a rendered harness-specific artifact.
4. `SupportTier`: tested/maturity status.
5. `TrustTier`: provenance/security posture.
6. `OpenSpecChange`: durable change proposal/design/task/spec-delta unit.
7. `Transaction`: config write with backup and rollback.

## Implementation anchors

Known public repo anchors include `pyproject.toml`, `wagents/`, `config/`, `instructions/`, `skills/`, `mcp/`, `.claude/`, `.cursor/`, `.opencode/`, `.codex-plugin/`, `.agents/`, `tests/`, and `docs/`.

## Acceptance criteria

- Canonical registries exist and are schema-validated.
- Harness adapters render from registries instead of duplicate hand-maintained config.
- Docs pages render from registry data.
- CI fails when generated docs/configs are stale.
- Every first-class harness has golden fixtures.
- OpenSpec changes are required for structural changes.
