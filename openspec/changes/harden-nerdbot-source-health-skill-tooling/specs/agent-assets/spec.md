# Nerdbot operation and package integrity

## ADDED Requirements

### Requirement: Repairable audit projection

Nerdbot SHALL treat its operation journal as the canonical mutation audit record
and SHALL update the human activity log as an idempotently repairable projection
under an exclusive operation lock.

#### Scenario: Interruption after journal append

- **GIVEN** a committed operation is present in the journal and absent from the activity log
- **WHEN** repair or the next mutating workflow runs
- **THEN** exactly one activity entry with that operation ID is materialized

### Requirement: Crash-recoverable operation state

Every applied Nerdbot workflow SHALL hold the project operation lock across its
complete batch. A persisted operation SHALL begin with `prepared`, preserve its
immutable payload, and end with exactly one `committed`, `failed`, or
`review-needed` transition. Replay and repair SHALL share the strict canonical
parser, and only committed operations SHALL receive an exact standalone activity
marker.

#### Scenario: Abrupt stop after a workflow data write

- **GIVEN** a matching operation is durable as `prepared` and only part of its intended data is present
- **WHEN** the identical intent is retried
- **THEN** byte-identical files and exact append-only rows are reconciled under the same operation ID
- **AND** exactly one terminal transition and at most one committed activity marker are written

#### Scenario: Forged marker text

- **GIVEN** target or summary input contains control, format, surrogate, newline, Unicode line/paragraph separator, or backtick text
- **WHEN** an operation entry is constructed or loaded
- **THEN** validation rejects it before journal or activity-log mutation
- **AND** marker-like legacy prose separated by a Unicode line/paragraph separator cannot suppress projection repair

### Requirement: Monotonic portable release

Nerdbot SHALL not lower its skill version below committed `1.0.0`, and its
portable archive SHALL exclude repo-only instruction files whose links or
commands cannot resolve after installation.

#### Scenario: Portable package dry-run

- **GIVEN** the Nerdbot skill is packaged from the repository
- **WHEN** portability and member-list checks run
- **THEN** its version is monotonic and repo-local `AGENTS.md` is absent
