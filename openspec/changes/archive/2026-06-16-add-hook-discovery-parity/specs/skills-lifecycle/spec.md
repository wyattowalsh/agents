# Skills Lifecycle Delta

## MODIFIED Requirements

### Requirement: Discover-skills uses skill-local discovery scripts

The `discover-skills` skill SHALL implement gap analysis, coordinator manifests, and scout artifact merge entirely under `skills/discover-skills/scripts/` without importing or referencing `wagents`.

#### Scenario: Hook scan delegates via subprocess (parity with inventory)

- **WHEN** `hook_scan.py` builds the semantic hook inventory for discover-skills
- **THEN** it SHALL invoke its collection logic (e.g. local stdlib helper or delegated script) via subprocess in the style of `inventory_scan.py`
- **AND** it SHALL NOT import `wagents` modules (enforced by test_skills_no_wagents + portable check).
- **AND** it SHALL produce `hook-scan.json` (or equivalent named artifact) that `validate_hook_scan` (and the hook-scan schema under `data/schemas/`) accepts.

## Notes

This delta adds the hook_scan parity requirement to match the intent of full discovery parity (MCP/plugin style) for the hooks dimension. The canonical source update lives at `openspec/specs/skills-lifecycle/spec.md`; this file records the change delta for OpenSpec tracking.
