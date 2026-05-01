## ADDED Requirements

### Requirement: Skills-first lifecycle

The skills lifecycle lane SHALL treat Agent Skills as the default portable capability model and require script conformance, provenance, and validation before promotion.

#### Scenario: Script-backed skill is reviewed

- **GIVEN** a skill contains executable scripts
- **WHEN** it is evaluated for promotion
- **THEN** it documents `--help`, `--json`, `--dry-run`, or a justified exception.
