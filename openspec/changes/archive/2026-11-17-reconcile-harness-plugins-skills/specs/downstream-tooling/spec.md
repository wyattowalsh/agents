# Downstream Tooling Delta

## ADDED Requirements

### Requirement: Plugin and extension reconciliation preserves user-owned state

The repository SHALL distinguish repo-managed plugin surfaces from user-owned
local plugins, extension directories, native plugin caches, and home config
drift.

#### Scenario: Native plugin cache drift is approval gated

- **GIVEN** a locally cached native plugin clone differs from the current repo
  source
- **WHEN** the reconciliation manifest is generated
- **THEN** the row SHALL be marked `cache-refresh-needed`
- **AND** the generator SHALL NOT delete or refresh the cache.

#### Scenario: Extension validation blockers are explicit

- **GIVEN** local harness config prevents reliable extension validation
- **WHEN** extension rows are written to the reconciliation matrix
- **THEN** affected rows SHALL be marked `config-repair-needed`
- **AND** the manifest SHALL preserve the extension names without exposing
  secrets or unredacted local absolute paths.
