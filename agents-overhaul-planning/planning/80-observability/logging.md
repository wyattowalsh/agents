---
status: planning
owner: platform-orchestrator
last_updated: 2026-05-01
principle: skills-first, specs-governed, mcp-when-live-state-required
---

# Structured Logging

## Objective

Implement structured logging for the multi-harness control plane.

## Data model

- timestamp
- component
- harness
- capability id
- transaction id
- status
- redacted details

## Acceptance criteria

- No secret values in output.
- JSON output available for automation.
- Human-readable summary available for CLI users.
