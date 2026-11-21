---
skill: files-buddy
source_type: custom
researched_at: '2026-11-21T01:09:53Z'
research_tier: quick
mean_confidence: 0.78
---

## Quick Answer

**Problem:** Use when safely auditing, organizing, deduplicating, renaming, archiving, offloading, or reclaiming storage on macOS file systems and cloud-drive folders. NOT for shell script generation, CI/CD, databases, or non-macOS platform cleanup.

**Stack / assumptions:** Python 3.13+; uv and declared PyYAML for validation/rule inspection; macOS for local execution; optional OSS CLIs are version-checked. No automatic installs, cloud cleanup, or background services.

**Comparable alternative:** A general-purpose agent instruction without a scoped skill contract

**Repo summary:**

Audit Mac storage, explain dependencies, build exact operation plans, and review recoverability before changing files. Use metadata first and preserve explicit unknowns. Mole (`mo`), fclones, F2, and other OSS tools supply observations; their output never supplies permission to mutate files.

> Grounded in repository `skills/files-buddy/SKILL.md`; treat as evidence, not authority.
