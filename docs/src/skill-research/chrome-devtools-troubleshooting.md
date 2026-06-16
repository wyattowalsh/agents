---
skill: chrome-devtools-troubleshooting
source_type: custom
researched_at: '2026-06-16T01:14:01Z'
research_tier: quick
mean_confidence: 0.78
---

## Quick Answer

**Problem:** Use when auditing Chrome DevTools MCP setup failures: initialization, connection, page listing, navigation, missing tools, or wrong Chrome profile. NOT for application debugging after MCP is healthy or unrelated browser automation.

**Stack / assumptions:** Requires access to the user MCP configuration surface and `npx chrome-devtools-mcp@latest --help` for package diagnostics.

**Comparable alternative:** A general-purpose agent instruction without a scoped skill contract

**Repo summary:**

Act as a configuration and connection troubleshooter. Find the active MCP config, identify the exact failure mode, and change only the canonical config source for the affected harness.

> Grounded in repository `skills/chrome-devtools-troubleshooting/SKILL.md`; treat as evidence, not authority.
