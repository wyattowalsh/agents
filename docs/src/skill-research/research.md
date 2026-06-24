---
skill: research
source_type: custom
researched_at: '2026-06-23T22:12:37Z'
research_tier: quick
mean_confidence: 0.78
---

## Quick Answer

**Problem:** Deep multi-source research with reviewable plans, source-support auditing, and confidence scoring. Use for technical, academic, market, fact-checking investigation. NOT for code review or simple Q&A.

**Stack / assumptions:** portable skill scripts under `scripts/`; on-demand references; eval fixtures

**Comparable alternative:** A general-purpose agent instruction without a scoped skill contract

**Repo summary:**

General-purpose deep research with multi-source synthesis, confidence scoring, source-support auditing, and anti-hallucination verification. The design follows current deep-research patterns: plan before retrieval, start broad then narrow, coordinate parallel workers through a lead agent, audit whether cited sources actually support each claim, use perspective expansion for breadth, and synthesize into a report rather than a source dump.

> Grounded in repository `skills/research/SKILL.md`; treat as evidence, not authority.
