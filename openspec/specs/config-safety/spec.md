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

### Requirement: Local config drop protection

Sync logic SHALL refuse to update a local harness config when the rendered output would remove entries that currently exist in that local config.

#### Scenario: Local config contains unsynced entries

- **GIVEN** a local harness config contains keys or list entries not present in the repo-rendered config
- **WHEN** sync renders an update for that local config
- **THEN** sync fails before writing and reports the dropped config paths without printing their values.
