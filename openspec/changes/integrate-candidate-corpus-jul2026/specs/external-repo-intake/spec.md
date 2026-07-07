# external-repo-intake Delta

## MODIFIED Requirements

### Requirement: External repos remain discovery inputs

The external repo intake lane SHALL create source, license, security,
provenance, docs-steward, and conformance-review tasks without installing or
promoting external assets by default.

#### Scenario: External repo is marked adopt-candidate

- **GIVEN** an external repo has initial action `adopt-candidates`
- **WHEN** intake runs
- **THEN** it remains uninstalled until all promotion gates pass.

#### Scenario: Bulk candidate corpus intake is processed

- **GIVEN** a tracked raw URL corpus contains external repos, tree targets,
  fragments, and duplicates
- **WHEN** candidate corpus intake runs
- **THEN** every raw entry SHALL be represented in a machine-readable record
- **AND** every unique normalized target SHALL have exactly one final discovery
  decision
- **AND** exact duplicate raw entries SHALL remain counted as covered raw
  entries
- **AND** no candidate SHALL be installed, executed, vendored, or promoted by
  the intake pass.

#### Scenario: Candidate docs-steward surfaces are mapped

- **GIVEN** a candidate has an intake decision
- **WHEN** docs impact is recorded
- **THEN** affected docs-steward surfaces SHALL be listed
- **AND** generated docs and catalog surfaces SHALL remain source-of-truth
  driven.

#### Scenario: Candidate catalog coverage is non-installable

- **GIVEN** a normalized candidate target is represented in the catalog
- **WHEN** docs generation and skills sync preview run
- **THEN** the catalog row SHALL publish no install command
- **AND** the catalog row SHALL use a non-syncing state
- **AND** skills sync preview SHALL not produce install commands for that row.

### Requirement: Candidate corpus promotion research packets are trust-gated

The external repo intake lane SHALL generate promotion research packet artifacts
that make the next review phase dispatchable without making candidates
installable, executable, vendored, promoted, or repo-mutation eligible.

#### Scenario: Research packet schema and graph are generated

- **GIVEN** the July 2026 candidate corpus has 293 raw entries and 289 unique
  normalized targets
- **WHEN** candidate corpus promotion research planning runs
- **THEN** the research graph SHALL contain one `U###` lane per raw entry
- **AND** one `N###` synthesis lane per unique normalized target
- **AND** every raw lane SHALL use the required raw packet leaf checks
- **AND** every synthesis lane SHALL use the required unique-target leaf checks
- **AND** the packet schema SHALL list required evidence fields including
  source, license, security, auth, attribution, blockers, install command,
  live install eligibility, docs-steward surfaces, and validation evidence.

#### Scenario: Promotion readiness remains blocked until trust gates pass

- **GIVEN** candidate corpus research packets are generated
- **WHEN** promotion readiness is summarized
- **THEN** `ready_for_repo_promotion` SHALL be zero unless trust-gate evidence
  is complete
- **AND** `ready_for_live_install` SHALL be zero unless an exact reviewed
  install command is recorded
- **AND** every blocked target SHALL include source-list, license, security,
  attribution, auth, docs-steward, and target-specific validation blockers
- **AND** no blocked target SHALL contain an install command.

#### Scenario: Promotion waves assign targets without mutation

- **GIVEN** the unique normalized targets are ready for read-only research
- **WHEN** promotion waves are generated
- **THEN** every unique normalized target SHALL be assigned to exactly one wave
- **AND** existing installable catalog coverage SHALL route to a no-mutation
  wave
- **AND** every non-existing-coverage wave SHALL require read-only research
  packet completion before a single integrator performs repo mutations.

#### Scenario: Existing integration coverage prevents duplicate catalog installability

- **GIVEN** a candidate is already covered by an existing installable curated
  catalog row
- **WHEN** the promotion wave plan is generated
- **THEN** the candidate corpus row SHALL remain non-installable
- **AND** the existing catalog row SHALL own installability
- **AND** promotion planning SHALL record a merge/no-duplicate decision instead
  of publishing another install command.
