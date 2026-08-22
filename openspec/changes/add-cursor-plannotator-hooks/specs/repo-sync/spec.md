# Delta: Home-copy Cursor Plannotator shim

## ADDED Requirements

### Requirement: Cursor home sync copies the Plannotator plan-hook shim

Repo home sync for Cursor SHALL copy `scripts/cursor/plannotator-plan-hook.py`
into `~/.cursor/hooks/plannotator-plan-hook.py` (executable, idempotent) when
Plannotator hooks are enabled. `--no-plannotator-hooks` SHALL skip both Grok
and Cursor Plannotator hook refresh.

#### Scenario: Shim copy is idempotent

- **WHEN** Cursor home sync runs twice with identical shim bytes
- **THEN** the destination SHALL remain executable
- **AND** sync SHALL NOT rewrite identical bytes

#### Scenario: Flag skips Grok and Cursor Plannotator

- **WHEN** `scripts/sync_agent_stack.py` is invoked with `--no-plannotator-hooks`
- **THEN** Grok `plannotator.json` SHALL NOT be refreshed
- **AND** Cursor Plannotator shim copy and hook merge SHALL NOT run
