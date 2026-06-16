---
skill: chrome-devtools-cli
source_type: custom
researched_at: '2026-06-16T01:14:01Z'
research_tier: quick
mean_confidence: 0.78
---

## Quick Answer

**Problem:** Use when auditing, writing, or running bounded shell commands that drive Chrome DevTools through the `chrome-devtools` CLI. NOT for MCP tool-call workflows, broad browser QA, unattended package installation, or replacing harness MCP configuration.

**Stack / assumptions:** Requires the `chrome-devtools` binary from chrome-devtools-mcp 0.23.0 or compatible version and Node.js 20.19.0, 22.12.0, or newer.

**Comparable alternative:** A general-purpose agent instruction without a scoped skill contract

**Repo summary:**

Use the `chrome-devtools` CLI for terminal-driven browser automation when the user explicitly needs shell commands or scripts. Prefer MCP tools directly when the current harness already exposes Chrome DevTools MCP tools.

> Grounded in repository `skills/chrome-devtools-cli/SKILL.md`; treat as evidence, not authority.
