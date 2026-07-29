# Delta: Final APM Lock Closure

## ADDED Requirements

### Requirement: APM lock proof is the final generation gate

RV-008 closure SHALL run `uv run wagents apm refresh-lock --check` only after
all docs, README, MCPHub, reconciliation, sync, materialization, and other APM
projection writers have finished. Earlier passing lock checks SHALL NOT count
as final evidence.

#### Scenario: All generators have settled

- **WHEN** every scheduled source-driven generator and materializer is complete
- **THEN** `uv run wagents apm refresh-lock --check` SHALL report no deployed
  path or hash drift
- **AND** its accepted evidence SHALL identify it as the final gate.

#### Scenario: A generator writes after the lock check

- **WHEN** any owned generator or materializer writes after a passing APM lock
  check
- **THEN** the earlier proof SHALL be invalidated
- **AND** the final lock check SHALL run again after the new settled state.
