# Skills Lifecycle Delta

## ADDED Requirements

### Requirement: Discover-skills uses skill-local discovery scripts

The `discover-skills` skill SHALL implement gap analysis, coordinator manifests, and scout artifact merge entirely under `skills/discover-skills/scripts/` without importing or referencing `wagents`.

#### Scenario: Inventory scan delegates via subprocess

- **WHEN** `inventory_scan.py` builds the repo skill inventory
- **THEN** it SHALL invoke `skills/skill-router/scripts/skill_index.py` via subprocess
- **AND** it SHALL NOT import `wagents` modules.

#### Scenario: Harness scan delegates via subprocess

- **WHEN** `invoke_surfaces.py` scans harness surfaces
- **THEN** it SHALL invoke `skills/harness-master/scripts/discover_surfaces.py` via subprocess
- **AND** it SHALL NOT import `wagents` modules.

### Requirement: Discovery artifacts are schema-validated

Discovery session outputs SHALL use JSON contracts validated by `schemas.py`, `validate_session.py`, and files under `data/schemas/`.

#### Scenario: Gap report validates before scouts

- **WHEN** Wave 0 completes and `gap-report.json` is produced
- **THEN** `validate_gap_report` SHALL accept the payload
- **AND** coordinator planning SHALL NOT run until the gap report exists.

#### Scenario: Coordinator enforces scout accounting

- **WHEN** `coordinator.py verify` runs for a wave manifest
- **THEN** `resolved_count` SHALL equal `expected_count` before ideation advances
- **AND** each resolved task SHALL have a scout artifact with `status` of `success` or `skipped`.

### Requirement: Wave 2 scout dispatch is capped

Coordinator wave-2 planning SHALL cap parallel scout tasks at 24.

#### Scenario: Large taxonomy produces bounded manifest

- **WHEN** `coordinator.py plan --wave 2` runs against the default taxonomy
- **THEN** `expected_count` SHALL be less than or equal to 24
- **AND** the manifest SHALL pass `validate_wave_manifest`.