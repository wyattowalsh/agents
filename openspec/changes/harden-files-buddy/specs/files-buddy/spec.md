## ADDED Requirements

### Requirement: Exact approved operations

Files Buddy SHALL bind local mutations to an exact reviewed mapping and fresh
object evidence, persist intent before effects, and never overwrite collisions.

#### Scenario: Scope changes after preview

- **GIVEN** a plan names an exact set of files
- **WHEN** another file appears or a planned file changes
- **THEN** the new file is excluded and the changed operation is blocked.

#### Scenario: Execution is interrupted

- **GIVEN** an operation has durable prepared intent
- **WHEN** execution stops before final verification
- **THEN** reconciliation reports observed evidence without blindly replaying it.

### Requirement: Truthful reports and observations

Files Buddy SHALL distinguish unknown evidence, candidate bytes, acted-on bytes,
retained Trash/quarantine bytes, verified outcomes, and observed free-space deltas.

#### Scenario: Zero verified bytes

- **GIVEN** completed bytes are nonzero and verified bytes are zero
- **WHEN** the dashboard renders
- **THEN** verified bytes remain zero and duplicate findings acquire no invented risk or restore guarantee.

#### Scenario: A tool returns partial coverage

- **GIVEN** a supported observation tool returns partial or unavailable scan status
- **WHEN** Files Buddy parses its JSON
- **THEN** it preserves that coverage and does not authorize any mutation.

### Requirement: Portable and behaviorally checked skill

Files Buddy SHALL validate from an isolated skill package with declared
dependencies and executable regression tests in addition to structural evals.

#### Scenario: Indexed reference is absent

- **GIVEN** an isolated package is missing an indexed reference
- **WHEN** its check command runs
- **THEN** the bundled package gate runs and fails.

#### Scenario: A native capability is unqualified

- **GIVEN** native provider or metadata semantics have no acceptance evidence
- **WHEN** the capability is requested
- **THEN** Files Buddy presents a review or native handoff and reports the limit.
