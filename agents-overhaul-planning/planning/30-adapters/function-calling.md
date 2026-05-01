---
status: planning
owner: platform-orchestrator
last_updated: 2026-05-01
principle: skills-first, specs-governed, mcp-when-live-state-required
---

# Function Calling Adapter

## Goal

Translate canonical tool schemas into JSON-schema/function-calling compatible forms where a harness supports direct tool calls.

## Constraints

- Preserve argument validation.
- Do not flatten semantics that affect safety.
- Keep generated schema diffs in CI.
