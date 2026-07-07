# external-repo-intake Delta

## MODIFIED Requirements

### Requirement: External repos remain discovery inputs

The external repo intake lane SHALL create source, license, security,
provenance, docs-steward, and conformance-review tasks without installing or
promoting external assets by default. A separate reviewed promotion overlay MAY
make candidates installable only after target-specific gates pass.

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

#### Scenario: Candidate catalog coverage is non-installable while terminal-gated

- **GIVEN** a normalized candidate target remains terminal-gated after review
- **WHEN** docs generation and skills sync preview run
- **THEN** the catalog row SHALL publish no install command
- **AND** the catalog row SHALL use a non-syncing state
- **AND** skills sync preview SHALL not produce install commands for that row.

#### Scenario: Candidate catalog coverage is promoted after review

- **GIVEN** a normalized candidate target has one or more reviewed Skills CLI
  selectors with source-list, license, security, attribution, auth, dedupe,
  docs-steward, and validation evidence
- **WHEN** the promotion overlay is applied
- **THEN** installable selectors SHALL be represented as curated-external
  catalog rows
- **AND** the install command SHALL use the reviewed selector
- **AND** local install evidence SHALL be recorded without committing secrets.

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

#### Scenario: Promotion overlay completes reviewed installable rows

- **GIVEN** promotion gates have passed for reviewed selectors
- **WHEN** the overlay is applied
- **THEN** the progress manifest SHALL mark the July 2026 corpus goal complete
- **AND** every raw entry SHALL remain accounted for
- **AND** every unique normalized target SHALL have a terminal decision
- **AND** remaining non-installable rows SHALL have explicit terminal blockers.

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
