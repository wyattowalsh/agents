---
status: planning
owner: platform-orchestrator
last_updated: 2026-05-01
principle: skills-first, specs-governed, mcp-when-live-state-required
---

# CLI Adapter

## Goal

Wrap harness CLIs and package managers in robust, scriptable commands.

## Preferred install surfaces

- `npx skills ...` for skill management.
- `uvx ...` for Python CLIs/MCPs.
- `npx -y ...` for Node CLIs/MCPs.

## CLI contract

- non-interactive mode when available
- JSON output when available
- explicit exit codes
- no secret printing
