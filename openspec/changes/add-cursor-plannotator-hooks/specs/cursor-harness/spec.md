# Delta: Cursor home Plannotator hooks

## ADDED Requirements

### Requirement: Cursor Plannotator hooks are home-only

The system SHALL project Plannotator plan-review hooks into user
`~/.cursor/hooks.json` and copy `scripts/cursor/plannotator-plan-hook.py` to
`~/.cursor/hooks/plannotator-plan-hook.py`. Project `.cursor/hooks.json` SHALL
NOT gain Plannotator rows. `cursor-cli` SHALL consume the same user hooks and
SHALL NOT be added to hook-registry render lists.

#### Scenario: Home sync installs Cursor-native matchers

- **WHEN** Cursor home sync runs with Plannotator hooks enabled
- **THEN** `~/.cursor/hooks.json` SHALL contain flat `preToolUse` rows matching
  `SwitchMode` (enter / improve-context, timeout 5, `failClosed` false) and
  `CreatePlan` (plan review, timeout 345600, `failClosed` false)

#### Scenario: Project hooks stay fleet-only

- **WHEN** repo Cursor hook projection runs
- **THEN** git-tracked `.cursor/hooks.json` SHALL NOT include Plannotator
  CreatePlan or SwitchMode commands

#### Scenario: Cloud agents do not load user Plannotator hooks

- **WHEN** a Cursor cloud agent starts
- **THEN** it SHALL NOT load `~/.cursor/hooks.json`
- **AND** the 345600s review hook SHALL remain home-local so cloud runs cannot hang on it

#### Scenario: Opt-out skips Cursor Plannotator rows

- **WHEN** home sync runs with `--no-plannotator-hooks`
- **THEN** the Cursor shim SHALL NOT be copied
- **AND** Plannotator rows SHALL NOT be merged into `~/.cursor/hooks.json`

### Requirement: Cursor Plannotator shim is fail-open

The home shim SHALL parse Cursor camelCase and snake_case tool payloads, review
inline `plan` then `overview` on `CreatePlan`, and run `plannotator
improve-context` only when `SwitchMode` targets `plan`. Missing binary, empty
plan, crash, or unmapped JSON SHALL allow. The shim SHALL NOT exit 2 and SHALL
NOT scan other projects' plan files.

#### Scenario: CreatePlan deny maps to Cursor permission JSON

- **WHEN** Plannotator returns a mapped deny or block decision
- **THEN** the shim SHALL print `{"permission": "deny", "agent_message": "..."}`
  with optional `user_message`
- **AND** the process exit code SHALL be 0

#### Scenario: SwitchMode to agent allows immediately

- **WHEN** `SwitchMode` `target_mode_id` is not `plan`
- **THEN** the shim SHALL allow without invoking Plannotator
