---
description: 'Path-scoped rule: skill-integrity.md'
applyTo: skills/**/SKILL.md,skills/**/references/*.md
---

Run the skill's portable validator after modifying any skill file: `uv run python skills/<name>/scripts/check.py` when present, otherwise `uv run python skills/skill-creator/scripts/asset_toolkit/validate_skill.py skills/<name>`.
