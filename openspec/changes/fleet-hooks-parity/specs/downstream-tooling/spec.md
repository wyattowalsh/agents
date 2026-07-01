# Downstream Tooling Delta

## ADDED Requirements

### Requirement: Hook registries are schema validated before projection

The repository SHALL validate repo-owned and externally-owned hook registry
sources with JSON Schema before using them to generate downstream harness hook
surfaces.

#### Scenario: Repo-owned hook registry is validated

- **GIVEN** `config/hook-registry.json` is edited
- **WHEN** the repository schema conformance tests run
- **THEN** the registry SHALL validate against `config/schemas/hook-registry.schema.json`
- **AND** forward-looking hook fields such as `logical_policy`, `projection`, and `harness_overrides` SHALL remain schema-recognized but optional.

#### Scenario: External hook registry is validated

- **GIVEN** `config/external-hooks-registry.json` records a third-party hook policy
- **WHEN** the repository schema conformance tests run
- **THEN** the registry SHALL validate against `config/schemas/external-hooks-registry.schema.json`
- **AND** repo-owned generated hook projection SHALL keep external hook provenance separate from `config/hook-registry.json`.

### Requirement: Cursor hook projection uses native flat entries

Cursor project hooks SHALL be rendered as flat per-event command entries and
SHALL use shell-expanded project paths instead of editor-only template tokens in
command strings.

#### Scenario: Cursor project hooks are generated

- **GIVEN** `scripts/sync_agent_stack.py --platforms cursor --targets repo` renders project hooks
- **WHEN** `.cursor/hooks.json` is written
- **THEN** each event entry SHALL contain a top-level `command`
- **AND** entries SHALL NOT use the nested Claude-style `hooks` group shape.

#### Scenario: Cursor executes a repo-owned wagents policy

- **GIVEN** a Cursor hook command is generated for a repo-owned wagents policy
- **WHEN** Cursor invokes the command string through the shell
- **THEN** the command SHALL call `"$CURSOR_PROJECT_DIR/hooks/run-wagents-hook" <policy-id> --harness cursor`
- **AND** the command SHALL NOT depend on `${workspaceFolder}` expansion.

#### Scenario: Cursor catch-all image optimization is not fail-closed before proof

- **GIVEN** the `image-input-optimizer-guard` policy is projected to Cursor with matcher `.*`
- **WHEN** the hook entry is rendered
- **THEN** the entry SHALL set `failClosed` to `false`
- **AND** narrower fail-closed enforcement SHALL require a verified command path and policy stdout contract.
