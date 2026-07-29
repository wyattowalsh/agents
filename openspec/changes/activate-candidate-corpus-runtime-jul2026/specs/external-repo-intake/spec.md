# Delta: Candidate Corpus Runtime Activation

## ADDED Requirements

### Requirement: Runtime completion is receipt-derived

The system SHALL report a candidate artifact as usable only when fresh identity,
install, semantic-use, failure-path, denial-path, fresh-process, rollback, and
promoted-final receipts all pass their registered predicates. Accepted leaves
SHALL be schema-valid ReceiptStore v2 records committed through owned-key
compare-and-swap and SHALL be invalidated by stale current-input or
installed-content digests.

#### Scenario: Path-only evidence is present

- **WHEN** an executable path, disabled configuration, inventory row, or dry-run
  plan exists without a semantic-use receipt
- **THEN** the artifact SHALL remain incomplete

#### Scenario: Rollback and reinstall pass

- **WHEN** the exact preimage is restored, fresh absence is observed, the
  artifact is reinstalled, and a fresh process uses it successfully
- **THEN** the artifact MAY reach promoted final state

#### Scenario: A receipt digest is stale

- **WHEN** a receipt's bound current-input digest or installed-content digest
  differs from the exact current artifact
- **THEN** the receipt SHALL NOT contribute to completion
- **AND** ReceiptStore v2 freshness evaluation SHALL retain the binding as
  incomplete.

### Requirement: Every applicable harness binding is exercised

The system SHALL compile exact selector-to-harness applicability edges and
SHALL require a distinct content-addressed proof chain for each binding. The
chain SHALL bind the exact selector, harness, current input digest, and
installed-content digest across exactly five phases: discovery; behavior with
positive and negative assertions; fresh-process use; rollback with absence,
restore, unchanged-state, and final-state proof; and promoted-final acceptance.
Required capabilities SHALL be derived from current portable catalog/sync
metadata, proved capabilities SHALL come only from accepted behavior receipts,
and untested capabilities SHALL equal `required - proved`.

#### Scenario: Aggregate inventory is green

- **WHEN** a whole-harness inventory reports no missing commands but an exact
  selector or artifact edge lacks a use receipt
- **THEN** full usability SHALL remain false

#### Scenario: Selector is already present

- **WHEN** sync inventory classifies an exact selector as `already_present` for
  a harness
- **THEN** the row SHALL count only as discovery evidence
- **AND** it SHALL NOT satisfy behavior, fresh-process, rollback, or
  promoted-final phases.

#### Scenario: A required capability is unproved

- **WHEN** current portable metadata derives a required capability that no
  accepted behavior receipt proves
- **THEN** the capability SHALL appear in the computed untested set
- **AND** the binding SHALL remain incomplete
- **AND** no producer SHALL replace the computed set with a hardcoded empty
  collection.

#### Scenario: One binding has complete proof

- **WHEN** one selector-to-harness binding has fresh accepted leaves for all
  five phases and every derived required capability
- **THEN** only that exact binding MAY reach promoted-final acceptance
- **AND** its receipts SHALL NOT be reused for another selector or harness.

### Requirement: Blockers never masquerade as completion

The system SHALL keep full usability false while any external credential,
license, platform, hardware, lawful-fixture, or supported-extension blocker is
active.

#### Scenario: Autonomous work is exhausted

- **WHEN** all safe autonomous work is complete and an operator action is still
  required
- **THEN** the system SHALL retain the exact blocker and resume node without
  claiming that everything is installed or usable

### Requirement: Behavioral receipts wait for safe process cleanup

Candidate CLI or plugin behavioral receipt generation SHALL remain blocked
until ordinary timeout paths prove process-group lifecycle cleanup:
TERM, bounded wait, KILL when needed, and final reap/drain.

#### Scenario: Process-group regression is not green

- **WHEN** an ordinary CLI/plugin timeout cleanup regression is failing,
  missing, or stale
- **THEN** candidate behavioral receipt regeneration SHALL NOT run
- **AND** existing receipts SHALL NOT be refreshed to conceal the blocker.

### Requirement: Independent review uses externally issued provenance

Live independent-review closure SHALL require externally issued session and
task provenance whenever a trusted harness issuer exists. Review source SHALL
reject issuer identities authored by the evidence producer itself. Distinct
actor or run strings alone SHALL NOT prove independence. This contract SHALL
NOT claim DSSE, SLSA, or in-toto compliance and SHALL NOT invent PKI.

#### Scenario: Trusted harness issuer is available

- **WHEN** a trusted harness can issue the review session and task identity
- **THEN** accepted review evidence SHALL bind that externally issued
  provenance to the reviewed input digest
- **AND** self-authored issuer identities SHALL be rejected.

#### Scenario: No trusted issuer is available

- **WHEN** repo-source review validation passes but no trusted harness issuer
  can provide external session/task provenance
- **THEN** source validation MAY pass
- **AND** live review closure SHALL remain `BLOCKED-EXTERNAL`
- **AND** the system SHALL NOT synthesize issuer identity or compliance claims.

### Requirement: Source-closed MCP activation remains regression-gated

RV-002 SHALL remain source-closed. Candidate MCP activation SHALL preserve
explicit registry `enabled: true`, registry/generated/live presence and
identity equality, authenticated MCPHub reachability, and unauthenticated
denial. This requirement introduces no new RV-002 implementation.

#### Scenario: Source-closed MCP proof is replayed

- **WHEN** RV-002 regression validation runs
- **THEN** registry, generated, and live entries SHALL all be present and
  enabled with equal normalized identity
- **AND** authenticated reachability SHALL succeed
- **AND** unauthenticated access SHALL be denied
- **AND** any regression SHALL reopen the gate without requesting a new feature.

### Requirement: Enabled plugins have reproducible immutable provenance

Every enabled candidate plugin SHALL bind a pinned upstream commit and Git tree,
an explicit source projection, a reviewed marketplace tree, an isolated install,
and the live cache to one approved content digest. Upstream reconstruction SHALL
read pinned Git objects rather than mutable worktree bytes. It SHALL accept only
regular file objects, preserve executable modes, reject symlinks and submodules,
and omit empty directories not represented by Git.

#### Scenario: Local executable residue appears

- **WHEN** generated bytecode or any other unapproved file appears in the
  marketplace source, isolated install, or live cache
- **THEN** plugin activation and rollback SHALL fail closed
- **AND** the residue SHALL NOT be added to the digest ignore policy.

#### Scenario: The working checkout cannot be cleanly materialized

- **WHEN** platform path semantics prevent a clean checkout but the pinned Git
  object database contains the audited commit and tree
- **THEN** the verifier SHALL reconstruct from those immutable objects
- **AND** unrelated checkout drift SHALL neither weaken nor block the proof.

### Requirement: Rollback acceptance follows the receipt-store CAS

Successful CLI, MCP, and plugin rollback evidence SHALL use an immutable
`commit-pending` journal followed by an immutable passed marker written only
after the receipt-store compare-and-swap succeeds. The marker SHALL bind the
journal path and digest, exact sorted unique artifact set, receipt revision,
receipt-store transaction, and receipt-document digest. Runtime consumers SHALL
read managed transcripts, journals, and markers once through no-follow
descriptor traversal.

#### Scenario: CAS succeeds but marker creation fails

- **WHEN** rollback receipts commit but no valid passed marker is written
- **THEN** the receipts SHALL remain incomplete
- **AND** a later run SHALL repair the proof without treating the markerless
  commit as accepted.

#### Scenario: Evidence traverses a symlink

- **WHEN** a transcript, journal, marker, or parent path traverses a symlink
- **THEN** the evidence SHALL be rejected before parsing or hashing
- **AND** an out-of-root target SHALL never satisfy the managed-path contract.
