---
skill: chrome-devtools-a11y-debugging
source_type: custom
researched_at: '2026-06-16T01:14:01Z'
research_tier: quick
mean_confidence: 0.78
---

## Quick Answer

**Problem:** Use when auditing web accessibility through Chrome DevTools MCP: semantic HTML, ARIA labels, focus order, keyboard navigation, tap targets, contrast, and Lighthouse failures. NOT for generic page debugging, non-browser policy writing, or performance optimization.

**Stack / assumptions:** Requires Chrome DevTools MCP 0.23.0 or compatible tools with `lighthouse_audit`, `take_snapshot`, `press_key`, `evaluate_script`, and console issue access.

**Comparable alternative:** A general-purpose agent instruction without a scoped skill contract

**Repo summary:**

Use Chrome DevTools MCP to validate what assistive technologies can see and how keyboard users move through the page. The accessibility tree is the primary source of truth; screenshots are supporting evidence.

> Grounded in repository `skills/chrome-devtools-a11y-debugging/SKILL.md`; treat as evidence, not authority.
