# Skill Registry Intake Delta

## ADDED Requirements

### Requirement: Local skill reconciliation evidence has terminal dispositions

The repository SHALL provide a redacted reconciliation manifest that accounts
for desired skills, installed external skills, and read-only discovered local
skills across supported harnesses.

#### Scenario: Default desired sync is fully accounted for

- **GIVEN** the reconciliation manifest is generated
- **WHEN** maintainers inspect `summary.skills.default_sync_missing_by_agent`
- **THEN** every supported Skills CLI adapter SHALL have a count field
- **AND** missing desired sync rows SHALL be represented separately from
  inventory query failures.

#### Scenario: Non-curated installed skills are not silently promoted

- **GIVEN** an installed skill has `installed-external` or
  `read-only-discovered` provenance
- **WHEN** it appears in the reconciliation matrix
- **THEN** it SHALL have a terminal local-only, catalog non-sync, or explicit
  approval-gated action
- **AND** it SHALL NOT be treated as a default desired sync row.
