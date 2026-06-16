---
skill: external-skill-auditor
source_type: custom
researched_at: '2026-06-16T01:14:01Z'
research_tier: quick
mean_confidence: 0.78
---

## Quick Answer

**Problem:** Audit third-party Agent Skills before install or repo promotion. Use when evaluating external skill sources, hooks, scripts, provenance, credentials, network behavior, or destructive commands. NOT for creating skills, code review, or appsec scans.

**Stack / assumptions:** portable skill scripts under `scripts/`; on-demand references; eval fixtures

**Comparable alternative:** A general-purpose agent instruction without a scoped skill contract

**Repo summary:**

Audit third-party Agent Skills as trust-bearing assets before installing them globally or promoting them into this repository.

> Grounded in repository `skills/external-skill-auditor/SKILL.md`; treat as evidence, not authority.
