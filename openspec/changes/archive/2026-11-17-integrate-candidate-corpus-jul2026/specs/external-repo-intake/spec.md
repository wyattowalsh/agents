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

#### Scenario: Stable public catalog ownership replaces candidate identities

- **GIVEN** the corpus contains 289 unique normalized targets
- **WHEN** stable public catalog reconciliation completes
- **THEN** all 289 targets SHALL resolve to stable non-candidate catalog owners
- **AND** the classification SHALL be exactly 121 existing installable owners,
  6 existing inspection-required owners, 158 generated stable references, and
  4 generated stable hard-quarantine references
- **AND** exactly 162 stable source-level references SHALL be generated
- **AND** public authoring, catalog indexes, and detail pages SHALL contain zero
  `candidate-corpus-*` identities.

#### Scenario: Stable integration is separate from installability

- **GIVEN** a target has a stable source-level catalog owner
- **WHEN** install eligibility is evaluated
- **THEN** the source-level reference SHALL NOT imply an install command
- **AND** generated stable references SHALL use `sync_kind: none`
- **AND** only separately reviewed selector rows MAY participate in skills sync.

#### Scenario: Hard-quarantine references remain docs-only

- **GIVEN** a source or tree target is one of the four central quarantine records
- **WHEN** its stable reference is generated or validated
- **THEN** the row MAY retain source attribution and safety review requirements
- **AND** it SHALL publish no install command or runtime target
- **AND** it SHALL NOT be installed, executed, or enabled by default
- **AND** any exception SHALL follow the central quarantine review workflow and
  require explicit user approval.

#### Scenario: Candidate catalog coverage is promoted after review

- **GIVEN** a normalized candidate target has one or more reviewed Skills CLI
  selectors with source-list, license, security, attribution, auth, dedupe,
  docs-steward, and validation evidence
- **WHEN** the promotion overlay is applied
- **THEN** installable selectors SHALL be represented as curated-external
  catalog rows
- **AND** the install command SHALL use the reviewed selector
- **AND** local install evidence SHALL be recorded without committing secrets.

### Requirement: Explicitly authorized runtime integration is inert and evidenced

The external repo intake lane SHALL keep installation disabled by default. A
separate runtime overlay MAY install an external CLI, library, MCP server, or
native plugin only after explicit maintainer authorization and target-specific
source, license, security, lifecycle-script, auth, and provenance review.

#### Scenario: Maintainer authorizes audited runtime installation

- **GIVEN** the intake and promotion gates have passed for a runtime artifact
- **AND** the maintainer explicitly authorizes local installation
- **WHEN** the runtime overlay installs or reconciles the artifact
- **THEN** the package version or source commit SHALL be pinned and recorded
- **AND** only audited lifecycle scripts SHALL run
- **AND** assurance SHALL use a bounded non-mutating probe or package inventory
  when no safe probe exists
- **AND** no credential value SHALL be written to repo evidence.

#### Scenario: Candidate MCP or broad-hook plugin is installed

- **GIVEN** an audited candidate contributes an MCP server or a plugin with
  lifecycle hooks
- **WHEN** it is registered on local harness surfaces
- **THEN** credentialed or high-risk MCP servers SHALL remain disabled and
  outside default groups
- **AND** broad-hook plugins SHALL remain installed-disabled
- **AND** optional auth SHALL be represented by environment-variable name only
- **AND** activation SHALL require a separate explicit target and risk review.

#### Scenario: Corpus target has no independent runtime

- **GIVEN** a normalized target is a skill-only source, collection, embedded
  helper, non-distributed library, policy conflict, or hard quarantine
- **WHEN** runtime assurance is generated
- **THEN** the target SHALL receive an explicit terminal runtime disposition
- **AND** it SHALL NOT be counted as a missing executable
- **AND** hard-quarantined targets SHALL have no installed or active runtime
  artifacts.

#### Scenario: Runtime assurance closes the corpus

- **GIVEN** the corpus contains 289 normalized targets
- **WHEN** the authorized runtime overlay completes
- **THEN** `non-skill-install-assurance.json` SHALL contain exactly one row per
  target
- **AND** every recorded runtime artifact SHALL be verified
- **AND** final raw records, progress, validation, and final review reports SHALL
  reference the assurance artifact and terminal runtime disposition.

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
- **THEN** the existing stable catalog row SHALL own source-level integration and
  installability
- **AND** no parallel candidate public row SHALL be emitted
- **AND** promotion planning SHALL record a merge/no-duplicate decision instead
  of publishing another install command.
