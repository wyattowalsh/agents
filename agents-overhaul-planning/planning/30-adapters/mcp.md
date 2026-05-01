---
status: planning
owner: platform-orchestrator
last_updated: 2026-05-01
principle: skills-first, specs-governed, mcp-when-live-state-required
---

# MCP Adapter

## Goal

Render MCP server configuration for clients that need live external-state access.

## Required behaviors

- support stdio and Streamable HTTP
- prefer `uvx` for Python and `npx -y` for Node
- env var references only
- include/exclude tool controls where supported
- transport warnings for SSE legacy behavior
- smoke-test tool discovery
