---
skill: chrome-devtools-memory-leak-debugging
source_type: custom
researched_at: '2026-06-16T01:14:01Z'
research_tier: quick
mean_confidence: 0.78
---

## Quick Answer

**Problem:** Use when auditing JavaScript, browser, or Node.js memory leaks with Chrome DevTools MCP heap snapshots, repeated interactions, memlab, and retainer traces. NOT for generic profiling, CPU regressions, or reading raw heap snapshots.

**Stack / assumptions:** Requires Chrome DevTools MCP 0.23.0 or compatible `take_memory_snapshot` support; memlab is optional and must be invoked with user-approved commands.

**Comparable alternative:** A general-purpose agent instruction without a scoped skill contract

**Repo summary:**

Use Chrome DevTools MCP to reproduce memory growth, capture heap snapshots, and analyze leaks without loading raw heap artifacts into the conversation.

> Grounded in repository `skills/chrome-devtools-memory-leak-debugging/SKILL.md`; treat as evidence, not authority.
