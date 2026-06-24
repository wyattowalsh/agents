# Skills Lifecycle Delta

## MODIFIED Requirements

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
