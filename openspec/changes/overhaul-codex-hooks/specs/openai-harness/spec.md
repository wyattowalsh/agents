# OpenAI Harness Delta

## ADDED Requirements

### Requirement: Codex hooks follow the official hook schema

Repo-managed Codex hook projection SHALL emit hook files and config that conform
to the current official Codex hook and config schemas.

#### Scenario: Codex hooks are rendered from the portable registry

- **GIVEN** a hook entry in `config/hook-registry.json` includes `codex` in its harness list
- **WHEN** Codex hooks are rendered
- **THEN** generated handlers SHALL include `type`, `command`, `timeout`, and `statusMessage`
- **AND** generated handlers SHALL include `commandWindows` only when configured
- **AND** generated handlers SHALL omit unsupported future or non-Codex handler fields.

#### Scenario: Local Codex hooks are preserved

- **GIVEN** `~/.codex/hooks.json` contains local non-generated hook entries
- **WHEN** repo-managed Codex hooks are merged
- **THEN** local non-generated entries SHALL remain
- **AND** stale generated `wagents-hook.py` entries SHALL be replaced.

#### Scenario: Codex guard policies return schema-compatible decisions

- **GIVEN** a Codex hook policy blocks a risky operation or asks Codex to continue
- **WHEN** the policy emits JSON
- **THEN** denial and stop-continuation decisions SHALL use Codex-compatible JSON fields.

#### Scenario: Codex quality and truth policies are conservative

- **GIVEN** Codex runs a repo-managed post-edit quality or stop truth-gate hook
- **WHEN** the hook emits feedback
- **THEN** post-edit quality feedback SHALL be model-visible context and SHALL NOT mutate files
- **AND** stop truth-gate feedback SHALL use `decision: "block"` only for final code-change claims that omit validation evidence.
