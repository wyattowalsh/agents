## ADDED Requirements

### Requirement: Portable skill validation

Each skill in PLAN_SKILL_IDS MUST ship scripts/check.py and bundled scripts/asset_toolkit/
sufficient to validate without sibling skill paths when SKILL_PORTABLE_CI=1.

#### Scenario: Portable CI check passes

- **WHEN** SKILL_PORTABLE_CI=1 and uv run python scripts/check.py runs from the skill directory
- **THEN** the command exits 0 using only bundled toolkit modules

### Requirement: P7 body operator paths

SKILL.md prose outside fenced code blocks MUST reference local scripts as scripts/<file> only.

#### Scenario: No repo-root script paths in prose

- **WHEN** find_nonportable_body_operator_lines() scans the SKILL.md body
- **THEN** zero matches are returned
