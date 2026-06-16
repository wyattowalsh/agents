---
skill: simplify
source_type: custom
researched_at: '2026-06-16T01:14:01Z'
research_tier: quick
mean_confidence: 0.78
---

## Quick Answer

**Problem:** Simplify working code without changing behavior. Analyze, apply, or explain clarity fixes. Use when recent code feels complex. NOT for review (honest-review) or debt scans (tech-debt-analyzer).

**Stack / assumptions:** Pre/Post hooks inspect edited files when metadata exists and no-op outside git repos. Stop hook intentionally runs repo-wide git diff --check hygiene inside git repos.

**Comparable alternative:** `honest-review` for review

**Repo summary:**

Simplify recently modified code for clarity, consistency, and maintainability while preserving exact behavior.

> Grounded in repository `skills/simplify/SKILL.md`; treat as evidence, not authority.
