---
status: planning
owner: platform-orchestrator
last_updated: 2026-05-01
principle: skills-first, specs-governed, mcp-when-live-state-required
---

# UI/UX Automation Plan

## Goal

Make the repository easy to use even though it targets many AI tools.

## UX principles

1. One command to diagnose.
2. One command to preview.
3. One command to apply safely.
4. One command to rollback.
5. One command to browse capabilities.
6. Docs and CLI should say the same thing because both render from registries.

## Proposed CLI

```text
wagents doctor
wagents sync --preview
wagents sync --apply
wagents rollback
wagents catalog browse
wagents catalog explain <capability-id>
wagents install-skill <skill-id>
wagents mcp inspect <server-id>
wagents openspec status
```

## UX surfaces

- terminal CLI
- generated docs site
- dashboard-style support matrix
- skill browser
- MCP live-state catalog
- OpenSpec change/task viewer
