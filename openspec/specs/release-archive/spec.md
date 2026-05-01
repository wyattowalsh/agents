# release-archive Specification

## Purpose
Define release, rollback, validation, release-note, and OpenSpec archive evidence required before closing the agents platform overhaul.
## Requirements
### Requirement: Release and archive readiness

The release/archive lane SHALL create rollout, migration, rollback, post-merge validation, release-note evidence, and OpenSpec archive checklists after earlier waves complete.

#### Scenario: Overhaul is ready to archive

- **GIVEN** all child lanes are complete and validated
- **WHEN** release/archive runs
- **THEN** it verifies docs, migrations, rollback, release evidence, and OpenSpec archive readiness before closing the parent change.
