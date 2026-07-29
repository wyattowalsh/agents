# Delta: ux-cli — sync buckets and compact reports

## ADDED Requirements

### Requirement: Skills sync reports store and projection buckets

`wagents skills sync` machine-readable output SHALL expose per-agent buckets that
distinguish store gaps from projection gaps, including at least:
`already_present`, `projection_ensure`, `projection_blocked`, `store_missing`,
`internal_projection`, and `skipped` (plus existing pin/unresolved fields during
transition). Default JSON SHALL prefer compact counts and samples; full name
lists MAY require `--verbose` or JSONL.

#### Scenario: Dry-run emits projection_ensure without applying

- **GIVEN** Cursor has store-present desired skills lacking
  `~/.cursor/skills/<name>`
- **WHEN** `uv run wagents skills sync --dry-run -a cursor --format json` runs
- **THEN** the report SHALL list those skills under `projection_ensure` (or
  equivalent nested agent bucket)
- **AND** the command SHALL NOT write home symlinks
- **AND** the process SHALL NOT exit 137 due to eager full-tree cleanup hashing
  on the happy path once lazy hashing is implemented.

#### Scenario: Store gaps remain Skills CLI commands

- **GIVEN** a desired skill has no readable `~/.agents/skills/<name>/SKILL.md`
- **AND** no preferred non-CLI owner covers the agent
- **WHEN** dry-run builds command groups
- **THEN** the skill SHALL appear under `store_missing` / install command groups
- **AND** SHALL NOT be classified solely as a projection ensure candidate.

#### Scenario: Apply wires ensure after CLI batches

- **GIVEN** an approved `wagents skills sync --apply` run includes Cursor
- **WHEN** Skills CLI batches complete
- **THEN** the CLI SHALL invoke `ensure_cursor_authoritative_links` for
  `projection_ensure` and `internal_projection` names
- **AND** a second apply SHALL be an idempotent no-op for already-correct links.
