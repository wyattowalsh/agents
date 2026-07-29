# Delta: skill-registry-intake — reconciliation store/projection keys

## ADDED Requirements

### Requirement: Reconciliation reports store and projection missing counts

The harness reconciliation evidence packet SHALL include per-agent counts that
cannot false-pass when canonical store presence exists without required
authoritative projection:

- `store_missing_by_agent`
- `projection_missing_by_agent`

These keys extend the sibling `reconcile-harness-plugins-skills` packet and
SHALL sit alongside existing `default_sync_missing_by_agent` fields. A baseline
reset is expected when the keys land; maintainers SHALL NOT treat legacy
“zero missing” alone as Cursor fully reconciled.

#### Scenario: Cursor store-only increments projection_missing

- **GIVEN** a desired skill is present under `~/.agents/skills/<name>`
- **AND** absent from `~/.cursor/skills/<name>`
- **WHEN** `scripts/generate_harness_reconciliation.py` regenerates the packet
- **THEN** `summary.skills.projection_missing_by_agent.cursor` SHALL count the
  skill
- **AND** `store_missing_by_agent.cursor` SHALL NOT count that skill solely for
  the projection gap.

#### Scenario: True store gap increments store_missing

- **GIVEN** a desired skill lacks a readable canonical store body
- **WHEN** the reconciliation summary is generated
- **THEN** `store_missing_by_agent` for the affected agent SHALL increment
- **AND** the row disposition SHALL remain approval-gated for any live install.

#### Scenario: Evidence path remains non-mutating

- **GIVEN** maintainers regenerate reconciliation evidence for this change
- **WHEN** the generator or dry-run sync runs
- **THEN** the workflow SHALL NOT run `wagents skills sync --apply`
- **AND** SHALL NOT run live `npx skills add`
- **AND** SHALL NOT perform mass home symlink writes.
