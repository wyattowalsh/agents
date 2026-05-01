# registry-core Specification

## Purpose
Define canonical registry vocabulary, schemas, and support tiers used by downstream validation, docs generation, and harness projection.
## Requirements
### Requirement: Canonical registry vocabulary

The registry core lane SHALL define registry schemas and freeze support tiers for downstream validation, docs generation, and harness projection.

#### Scenario: Support tiers are consistent

- **GIVEN** a registry entry is created
- **WHEN** its support tier is validated
- **THEN** it uses one of `validated`, `repo-present-validation-required`, `planned-research-backed`, `experimental`, `unverified`, `unsupported`, or `quarantine`.
