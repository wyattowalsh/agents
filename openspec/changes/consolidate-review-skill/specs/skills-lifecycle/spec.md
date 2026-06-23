# Skills Lifecycle Delta

## MODIFIED Requirements

### Requirement: Skills-first lifecycle

The skills lifecycle lane SHALL treat Agent Skills as the default portable
capability model and require script conformance, provenance, eval coverage,
canonical routing, and validation before promotion.

#### Scenario: Canonical review skill consolidates overlapping workflows

- **GIVEN** the repo introduces `skills/review/` as the canonical first-party
  review workflow
- **WHEN** legacy review-oriented skill entrypoints are removed
- **THEN** no active compatibility wrapper skill directory, catalog row,
  generated install script, or `/`-invocable surface remains for
  `honest-review`, `simplify`, or `external-skill-auditor`
- **AND** remaining review-oriented agents or docs delegate to `/review` or a
  scoped `/review <mode>`
- **AND** eval, docs, README, catalog, sync dry-run, and package checks pass
  before the change is considered ready.
