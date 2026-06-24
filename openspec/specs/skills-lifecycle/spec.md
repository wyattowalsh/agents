# skills-lifecycle Specification

## Purpose
Define lifecycle requirements for skill creation, packaging, validation, promotion, installation, and update safety.
## Requirements
### Requirement: Skills-first lifecycle

The skills lifecycle lane SHALL treat Agent Skills as the default portable capability model and require script conformance, provenance, and validation before promotion.

#### Scenario: Script-backed skill is reviewed

- **GIVEN** a skill contains executable scripts
- **WHEN** it is evaluated for promotion
- **THEN** it documents `--help`, `--json`, `--dry-run`, or a justified exception.

#### Scenario: Curated external skill is promoted

- **GIVEN** a third-party skill is considered for Install Now After Trust Gate
- **WHEN** maintainers record or update the curated entry
- **THEN** the entry SHALL include source-list evidence, license or license gap, audited head or no-pin rationale, executable-surface notes, allowed-tools/hooks/scripts notes where present, target agents, unsupported adapters where known, dedupe notes where overlap exists, risk notes, and promotion policy
- **AND** validation SHALL reject promotion when the source is hard-quarantined.

#### Scenario: Curated external evidence debt is measured

- **WHEN** maintainers need to plan remediation across curated external entries
- **THEN** they SHALL use a read-only catalog audit report before enabling strict validation gates
- **AND** strict catalog-audit failure SHALL be opt-in until the existing curated catalog rows have enough evidence to avoid known false failures.

#### Scenario: External skill sync is previewed

- **WHEN** curated external install commands or target agents change
- **THEN** maintainers SHALL run `uv run wagents skills sync --dry-run`
- **AND** SHALL NOT run `uv run wagents skills sync --apply` or live `npx skills add ...` unless the maintainer explicitly requests live installation.

#### Scenario: Skills CLI inventory query stalls

- **WHEN** a Skills CLI installed-inventory query fails, times out, or returns unusable JSON for a supported harness with a known local skill root
- **THEN** `wagents skills sync --dry-run` MAY continue with a read-only local `SKILL.md` root scan for that harness
- **AND** the sync report SHALL label the result with a warning so maintainers know the row classification used fallback evidence rather than authoritative Skills CLI output.

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

