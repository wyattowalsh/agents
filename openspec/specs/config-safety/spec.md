# config-safety Specification

## Purpose
Define safe configuration transaction, rollback, redaction, and live-config handling requirements for harness-managed surfaces.
## Requirements
### Requirement: Transaction-safe config changes

The config safety lane SHALL define preview, backup, apply, validate, and rollback semantics for harness configuration writes.

#### Scenario: Config apply fails validation

- **GIVEN** a config transaction writes a projected harness file
- **WHEN** post-apply validation fails
- **THEN** rollback restores the prior snapshot and reports the failure.
