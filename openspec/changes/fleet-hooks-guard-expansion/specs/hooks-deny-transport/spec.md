# Hooks Deny Transport Delta

## ADDED Requirements

### Requirement: OpenCode bridge deny transport

The OpenCode wagents hook bridge MUST observe dispatcher deny JSON: when
`run-wagents-hook` is invoked with `--harness opencode`, the dispatcher SHALL emit
deny decisions as JSON on stdout with exit code 0 so the bridge `isDeny()` check
can block tool execution.

#### Scenario: OpenCode read of secret file is denied

- **GIVEN** `cursor-before-read-file-guard` is invoked with `--harness opencode`
- **WHEN** the payload requests reading `.env`
- **THEN** stdout SHALL contain JSON with `permission: deny` or equivalent `isDeny` shape
- **AND** exit code SHALL be 0

### Requirement: Grok fleet hooks emit block JSON on deny

When `run-wagents-hook` is invoked with `--harness grok-build`, deny responses SHALL
use `decision: block` per `grok_deny_adapter.grok_deny_payload`.

#### Scenario: Grok fleet destructive shell is blocked

- **GIVEN** a fleet-projected enforce policy runs with `--harness grok-build`
- **WHEN** the payload contains a destructive shell command
- **THEN** stdout SHALL include `"decision":"block"`
- **AND** exit code SHALL be 0

### Requirement: Enforce policy module load failure

The dispatcher MUST deny rather than allow when a registry hook has `mode: enforce`
and its policy module fails to load.

#### Scenario: Read guard module missing

- **GIVEN** `evaluate_before_read_file` is unavailable
- **WHEN** `cursor-before-read-file-guard` runs for an enforce-tier registry row
- **THEN** the dispatcher SHALL emit a deny response
