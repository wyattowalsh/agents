---
description: 'Path-scoped rule: skill-validation.md'
applyTo: skills/*/SKILL.md
---

After modifying any SKILL.md:
1. Run `uv run python skills/<name>/scripts/check.py` when present, otherwise `uv run python skills/skill-creator/scripts/asset_toolkit/validate_skill.py skills/<name>`
2. Run `uv run python skills/skill-creator/scripts/audit.py <skill-name>` — score >= 80
3. Verify body under 500 lines (below frontmatter)
4. Verify description under 200 characters
5. NOT-for exclusions must name the correct alternative skill in parentheses — e.g., `NOT for CI/CD pipelines (devops-engineer)`
