# Skills Lifecycle Delta

## MODIFIED Requirements

### Requirement: Harness-master discovery uses skill-local discovery scripts

The `harness-master` skill SHALL implement gap analysis, coordinator manifests, scout artifact merge, surface/usage probes, and harness-bounded ecosystem research entirely under `skills/harness-master/scripts/discovery/` (and peer `scripts/` modules) and `data/discovery/` without importing or referencing `wagents`.

#### Scenario: Inventory scan delegates via subprocess

- **WHEN** `inventory_scan.py` (under `skills/harness-master/scripts/discovery/`) builds the repo skill inventory
- **THEN** it SHALL invoke `skills/skill-router/scripts/skill_index.py` via subprocess
- **AND** it SHALL NOT import `wagents` modules.

#### Scenario: Harness scan delegates via subprocess (or direct in-package post-merge)

- **WHEN** `invoke_surfaces.py` (under discovery/) scans harness surfaces
- **THEN** it SHALL invoke `skills/harness-master/scripts/discover_surfaces.py` (via subprocess for portable check parity, or direct relative import inside the unified skill)
- **AND** it SHALL NOT import `wagents` modules.

#### Scenario: Hook scan delegates via subprocess (parity with inventory)

- **WHEN** `hook_scan.py` (under `skills/harness-master/scripts/discovery/`) builds the semantic hook inventory for harness-master discovery
- **THEN** it SHALL invoke its collection logic (e.g. local stdlib helper `_hook_collect.py` or delegated script) via subprocess in the style of `inventory_scan.py`
- **AND** it SHALL NOT import `wagents` modules (enforced by test_skills_no_wagents + portable check).
- **AND** it SHALL produce `hook-scan.json` (or equivalent named artifact) that `validate_hook_scan` (and the hook-scan schema under `data/discovery/schemas/`) accepts.

#### Scenario: Gap engine, coordinator, and journal use harness-master paths

- **WHEN** `gap_engine.py`, `coordinator.py`, `journal-store.py`, `validate_session.py`, or `parity_check.py` execute under the discovery pipeline
- **THEN** they SHALL resolve taxonomy, schemas, and output under `skills/harness-master/data/discovery/` and write journals/artifacts to `~/.agents/harness-master/discovery/<sid>/`
- **AND** the skill SHALL continue to satisfy the no-wagents import rule and schema validation contracts.

## Notes

This delta supersedes the prior "Discover-skills uses skill-local discovery scripts" requirement (and its hook parity scenario) by moving authoritative ownership into `harness-master` under the `scripts/discovery/` + `data/discovery/` layout. The canonical source update lives at `openspec/specs/skills-lifecycle/spec.md`; this file records the change delta for OpenSpec tracking. Harness-bounded research and inferred discovery modes are part of the unified harness-master surface; standalone `skills/research/` remains out of scope for this requirement.
