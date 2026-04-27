---
name: Skill Audit
description: Audit a skill file for AGENTS.md compliance — check frontmatter, naming, description length, and body quality.
---

## Task
Audit the provided skill file against the repo's AGENTS.md compliance standards.

## Checklist
1. **Frontmatter completeness**
   - `name` present, kebab-case (`^[a-z0-9][a-z0-9-]*$`), ≤64 chars, matches directory name
   - `description` present, non-empty, ≤1024 chars
   - Optional fields valid: `license` (SPDX), `compatibility` (≤500 chars), `metadata.author`, `metadata.version` (semver), `metadata.internal` (boolean)
   - No unknown required fields missing

2. **Naming consistency**
   - File path: `skills/<name>/SKILL.md` where `<name>` == frontmatter `name`
   - Directory name matches frontmatter exactly

3. **Description quality**
   - Length between 50–1024 characters
   - Describes *what* the skill does, not just *how*
   - Uses imperative voice for action phrases ("Check the logs" not "Checks the logs")
   - No markdown formatting inside the description string

4. **Body quality**
   - Has substantive content beyond frontmatter (≥200 chars recommended)
   - Uses markdown headers for structure
   - Actionable instructions (numbered steps, checklists, or imperative commands)
   - References `$ARGUMENTS`, `$N`, or `` !`command` `` substitutions where applicable
   - No self-attribution or signatures

## Output Format
Return a concise audit report:
- **Status**: PASS / FAIL / WARN
- **Issues**: Bulleted list of violations with line references if available
- **Fixes**: Specific edit suggestions to bring the skill into compliance
- **Score**: X/10 based on coverage of the checklist above
