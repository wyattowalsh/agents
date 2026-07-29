# Delta: Ordinary Candidate Process Lifecycle

## ADDED Requirements

### Requirement: Ordinary candidate timeouts clean the POSIX process group

Ordinary candidate CLI and plugin runners SHALL start each timed operation in a
dedicated POSIX process group. On timeout they SHALL send TERM to that group,
wait for a fixed bounded grace interval, send KILL to the same group when any
member remains, then reap the direct child and drain stdout/stderr before
returning timeout evidence.

#### Scenario: Process group exits during the TERM grace period

- **WHEN** an ordinary CLI or plugin child times out and all group members exit
  after group TERM
- **THEN** the runner SHALL reap the direct child and drain both output pipes
- **AND** it SHALL NOT signal the parent agent's process group
- **AND** it SHALL return only after cleanup is complete.

#### Scenario: Descendant survives TERM

- **WHEN** a timed-out process-group descendant remains after the bounded TERM
  grace period
- **THEN** the runner SHALL send KILL to that same dedicated process group
- **AND** it SHALL reap the direct child and drain both output pipes
- **AND** a later probe SHALL observe neither the child nor descendant alive.

#### Scenario: Lifecycle cleanup is described

- **WHEN** docs or receipts describe the timeout control
- **THEN** they SHALL call it process lifecycle cleanup
- **AND** they SHALL NOT claim sandbox, filesystem, credential, or network
  isolation.

### Requirement: Behavioral receipt regeneration depends on lifecycle proof

Candidate behavioral receipt producers SHALL NOT regenerate or refresh ordinary
CLI/plugin evidence until the process-group cleanup regressions are present,
passing, and fresh.

#### Scenario: Cleanup proof is missing or failing

- **WHEN** the ordinary process-group lifecycle regression is missing, stale, or
  failing
- **THEN** behavioral receipt regeneration SHALL remain blocked
- **AND** existing receipt timestamps or digests SHALL NOT be refreshed to hide
  the blocker.
