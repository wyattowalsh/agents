---
status: planning
owner: platform-orchestrator
last_updated: 2026-05-01
principle: skills-first, specs-governed, mcp-when-live-state-required
---

# Browser / Runtime Adapter

## Goal

Model browser automation as MCP/plugin-backed live-runtime validation, not as a static skill.

## Candidate tools

- Chrome DevTools MCP
- Playwright MCP
- Antigravity browser surface if contract verified

## Safety

- isolate browser profiles
- never pass secrets through screenshots/logs
- avoid production URLs by default
