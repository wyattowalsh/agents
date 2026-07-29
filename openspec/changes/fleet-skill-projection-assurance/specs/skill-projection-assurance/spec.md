# Skill Projection Assurance Spec

## ADDED Requirements

### Requirement: Cursor presence distinguishes store from projection

The system MUST treat Skills CLI universal store presence as distinct from
Cursor home projection presence. Cursor global projection MUST be
`~/.cursor/skills/<name>` only. Paths under a repo's `.cursor/skills/**` MUST
NOT count as global Cursor coverage.

#### Scenario: Store-only is not covered

- **GIVEN** a skill body exists under `~/.agents/skills/<name>`
- **AND** `~/.cursor/skills/<name>` is absent
- **WHEN** presence is evaluated for Cursor
- **THEN** `store_present` is true, `projection_present` is false, and the
  presence tier is `store_only`

### Requirement: Sync planner Cursor already_present gate

`wagents skills sync` MUST mark a Cursor skill `already_present` only when a
preferred non-CLI owner covers it, or when both store and Cursor home
projection are present.

#### Scenario: Store-only becomes projection_ensure

- **GIVEN** a desired syncable skill with store body and no Cursor projection
- **WHEN** dry-run targets Cursor
- **THEN** the skill is listed under `projection_ensure` (or `projection_blocked`
  when ensure would refuse)
- **AND** it is not listed under `already_present`

### Requirement: Apply wires Skills CLI then Cursor ensure

On `--apply`, the system MUST run Skills CLI batches for `store_missing` only,
then MUST call `ensure_cursor_authoritative_links` with `dry_run=False` for
Cursor `projection_ensure` names (including newly installed store names).

#### Scenario: Projection ensure after store install

- **GIVEN** Cursor has `store_missing` and `projection_ensure` buckets
- **WHEN** apply succeeds for Skills CLI batches
- **THEN** Cursor authoritative links are ensured for both buckets' names
- **AND** Codex plugin / OpenCode `skills.paths` owner skips remain non-CLI

### Requirement: Compact sync JSON by default

Default `--format json` output MUST emit compact bucket payloads (count +
sample) unless `--verbose` is set.

#### Scenario: Compact cursor dry-run

- **GIVEN** a large Cursor dry-run inventory
- **WHEN** `--format json` is used without `--verbose`
- **THEN** each bucket reports `count` and a bounded `sample`
- **AND** full item lists are omitted

### Requirement: Reconciliation splits store vs projection missing

The harness reconciliation generator MUST publish `store_missing_by_agent` and
`projection_missing_by_agent`. Cursor MUST NOT report zero missing solely
because the universal store is populated.

#### Scenario: Cursor projection gap counted

- **GIVEN** a desired skill with store presence and missing `~/.cursor/skills`
- **WHEN** reconciliation skill rows are generated
- **THEN** Cursor increments `projection_missing_by_agent`
- **AND** Cursor is included in `default_sync_missing_by_agent`
