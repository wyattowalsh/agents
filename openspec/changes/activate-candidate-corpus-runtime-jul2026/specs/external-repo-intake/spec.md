# Delta: Candidate Corpus Runtime Activation

## ADDED Requirements

### Requirement: Runtime completion is receipt-derived

The system SHALL report a candidate artifact as usable only when fresh identity,
install, semantic-use, failure-path, denial-path, fresh-process, rollback, and
promoted-final receipts all pass their registered predicates.

#### Scenario: Path-only evidence is present

- **WHEN** an executable path, disabled configuration, inventory row, or dry-run
  plan exists without a semantic-use receipt
- **THEN** the artifact SHALL remain incomplete

#### Scenario: Rollback and reinstall pass

- **WHEN** the exact preimage is restored, fresh absence is observed, the
  artifact is reinstalled, and a fresh process uses it successfully
- **THEN** the artifact MAY reach promoted final state

### Requirement: Every applicable harness binding is exercised

The system SHALL compile exact artifact-harness applicability edges and SHALL
require discovery, positive use, negative use, fresh process, rollback absence,
and promoted-final receipts for every applicable edge.

#### Scenario: Aggregate inventory is green

- **WHEN** a whole-harness inventory reports no missing commands but an exact
  selector or artifact edge lacks a use receipt
- **THEN** full usability SHALL remain false

### Requirement: Blockers never masquerade as completion

The system SHALL keep full usability false while any external credential,
license, platform, hardware, lawful-fixture, or supported-extension blocker is
active.

#### Scenario: Autonomous work is exhausted

- **WHEN** all safe autonomous work is complete and an operator action is still
  required
- **THEN** the system SHALL retain the exact blocker and resume node without
  claiming that everything is installed or usable
