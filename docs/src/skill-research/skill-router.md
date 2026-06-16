---
skill: skill-router
source_type: custom
researched_at: '2026-06-16T01:14:01Z'
research_tier: quick
mean_confidence: 0.78
---

## Quick Answer

**Problem:** Route tasks to local skills. Use when choosing skills, recovering omitted skills after context warnings, or preparing a small skill context packet. NOT for install, authoring, or audit workflows.

**Stack / assumptions:** Requires Python 3.11+ with PyYAML; reads local SKILL.md files from repo, Codex, global, plugin, and supported agent skill roots via scripts/skill_index.py.

**Comparable alternative:** A general-purpose agent instruction without a scoped skill contract

**Repo summary:**

Use local skill indexing to choose and load relevant skills only when a task needs them.

> Grounded in repository `skills/skill-router/SKILL.md`; treat as evidence, not authority.
