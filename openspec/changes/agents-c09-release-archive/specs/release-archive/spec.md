## ADDED Requirements

### Requirement: Release and archive readiness

The release/archive lane SHALL create rollout, migration, rollback, post-merge validation, and OpenSpec archive checklists after earlier waves complete.

#### Scenario: Overhaul is ready to archive

- **GIVEN** all child lanes are complete and validated
- **WHEN** release/archive runs
- **THEN** it verifies docs, migrations, rollback, and OpenSpec archive readiness before closing the parent change.
