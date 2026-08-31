# Things++ Specification Delta

## ADDED Requirements

### Requirement: Things++ composes one complete typed Things capability

The repository SHALL compose Things++ from internal servers `things-core`, `things-shortcuts`, and `things-native` behind exactly one client-facing MCPHub group named `things`.

#### Scenario: The qualified union is complete and unique

- **GIVEN** the audited manifests declare 41 core, 21 Shortcuts, and 8 native tools
- **WHEN** the Things++ capability closure and generated MCPHub `tools/list` are validated
- **THEN** the qualified union SHALL contain exactly 70 unique operations
- **AND** every operation SHALL have a closed input/output schema, safety class, minimum scope, annotation, and test identifier.

#### Scenario: Arbitrary execution is rejected

- **WHEN** a caller supplies a raw Things URL, raw JSON command, generic Shortcut name, arbitrary AppleScript, shell, SQL, filesystem path, or uncontrolled UI instruction
- **THEN** the Things++ stack SHALL reject the request before backend execution
- **AND** SHALL NOT use a hidden passthrough fallback.

### Requirement: The SupaThings migration expands capability without loss

The canonical capability ledger SHALL map all 37 SupaThings outcomes, all 17 `things-manager` workflows, and all 25 legacy eval concepts to tested Things++ routes with no removed row and at least one net-new outcome.

#### Scenario: Coverage closure gates cutover

- **GIVEN** the frozen SupaThings, workflow, and eval baselines
- **WHEN** the migration closure check runs
- **THEN** each baseline row SHALL be classified `implemented`, `safe-replacement`, or `semantic-skill`
- **AND** no row SHALL be classified `removed`, missing, or untested
- **AND** the net-new tested outcome count SHALL be greater than zero.

The canonical ledger encodes this classification as a total mapping: `direct` and `composed` mapping kinds mean `implemented`, `safe-replacement` means `safe-replacement`, and `semantic` means `semantic-skill`. No other mapping kind is valid.

#### Scenario: Unsupported capabilities remain truthful

- **WHEN** a user requests recurrence-template editing or deterministic positional reordering
- **THEN** Things++ SHALL report the operation unsupported
- **AND** SHALL NOT fabricate support through URL, database, AppleScript, Shortcut, or UI passthrough.

### Requirement: Things++ serializes and verifies writes across backends

Every Things++ mutation SHALL use ID-first fresh state, the applicable preview/confirmation policy, cross-backend serialization, bounded execution, and a structured read-after-write result.

#### Scenario: A stale or partial write is detected

- **GIVEN** the target state changes after preview or a backend returns a partial result
- **WHEN** the write coordinator re-reads and verifies the target
- **THEN** it SHALL stop or report the mismatch as failed/ambiguous
- **AND** SHALL NOT claim unverified fields as changed.

#### Scenario: Private Things content contains instructions

- **GIVEN** a title, note, checklist, tag, error, or backend response contains tool instructions
- **WHEN** the skill or MCP adapter processes that content
- **THEN** it SHALL treat the content as untrusted data
- **AND** SHALL NOT expand scope, bypass approval, or persist the content in logs/docs/eval evidence.

### Requirement: Server-executed mutations use two-phase receipts

Every server-executed mutating public tool SHALL retain its tool name and closed domain schema while accepting the shared `preview`/`execute` mutation envelope enforced by `packages/things-common`. `things-shortcuts/create_todo_with_quick_entry` is the sole exception because it performs only a user-controlled UI handoff, not a server-verifiable mutation.

#### Scenario: A preview receipt is executed

- **GIVEN** preview freshly read the targets under the cross-backend reservation and issued a five-minute opaque single-use receipt
- **WHEN** execute presents the receipt
- **THEN** the server SHALL atomically verify principal, client, exact resource, tool, targets, canonical arguments, fresh-state hash, and independent minimum scope
- **AND** execute plus readback SHALL finish within the same serializable reservation.

#### Scenario: A receipt is replayed or substituted

- **WHEN** a receipt is expired, consumed, replayed, stale, or used with a different principal, client, resource, tool, target, argument, or scope
- **THEN** the server SHALL reject it before backend mutation
- **AND** a crash in `executing` SHALL be verified and reported changed/ambiguous without automatic replay.

#### Scenario: Quick Entry hands control to the user

- **WHEN** `create_todo_with_quick_entry` opens Things Quick Entry
- **THEN** it SHALL require UI approval, SHALL NOT target a heading, and SHALL return no changed item before the user saves
- **AND** it SHALL report handoff status without fabricating execute/readback or mutation-receipt evidence.

### Requirement: Shared mutation state resists filesystem and concurrency attacks

`packages/things-common` SHALL be a non-server library imported by exactly three backends and providing 0700 per-user runtime state, 0600 state files, an owner-checked non-symlink advisory lock, opaque receipt storage, serialization, redaction, and artifact verification.

#### Scenario: Runtime state or a backend races

- **WHEN** concurrent backends, a crash, symlink substitution, inode replacement, or TOCTOU mutation is detected
- **THEN** the common library SHALL fail closed or recover to a verified ambiguous state
- **AND** no two Things++ writes SHALL execute concurrently.
