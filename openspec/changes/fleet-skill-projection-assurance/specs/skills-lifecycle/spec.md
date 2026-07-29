# Delta: skills-lifecycle — fleet skill projection assurance

## ADDED Requirements

### Requirement: Skill sync presence splits store from projection

Fleet skill sync SHALL classify desired skills per agent using an explicit
presence model that separates canonical-store presence from harness
authoritative projection, and SHALL emit sync buckets that cannot treat
store-only Cursor coverage as fully synced.

Frozen coverage classes: `store_present`, `projection_present`,
`preferred_non_cli`, `secondary_only`, `missing`.

Frozen sync buckets: `already_present`, `projection_ensure`,
`projection_blocked`, `store_missing`, `internal_projection`, `skipped`.

#### Scenario: Cursor store-only is not already_present

- **GIVEN** a desired skill has a readable body under `~/.agents/skills/<name>`
- **AND** `~/.cursor/skills/<name>` is absent
- **AND** no preferred non-CLI owner covers Cursor for that skill
- **WHEN** `wagents skills sync --dry-run -a cursor` builds the planner report
- **THEN** the skill SHALL NOT be classified `already_present`
- **AND** it SHALL be classified `projection_ensure` when the link is safe
- **OR** `projection_blocked` when conflict rules apply.

#### Scenario: Preferred non-CLI owner short-circuits CLI and ensure

- **GIVEN** a repo-owned skill is covered by Codex plugin ownership or OpenCode
  `skills.paths` direct-repo-path ownership for the target agent
- **WHEN** the sync planner classifies the skill for that agent
- **THEN** the skill SHALL be `already_present` for reason `preferred_non_cli`
- **AND** the planner SHALL NOT emit a Skills CLI install command for that
  agent/skill pair
- **AND** the planner SHALL NOT require a harness-dir projection fill for that
  pair by default.

#### Scenario: Internal skills never re-enter Skills CLI

- **GIVEN** a desired skill has `metadata.internal: true` and a readable store
  body
- **AND** Cursor authoritative projection is missing
- **WHEN** the sync planner classifies the skill for Cursor
- **THEN** the skill SHALL be classified `internal_projection`
- **AND** the planner SHALL NOT include the skill in Skills CLI argv
- **AND** projection ensure from store SHALL remain the only install path.

#### Scenario: Project Cursor skills do not satisfy global coverage

- **GIVEN** only `.cursor/skills/repo/<name>` (or other project
  `.cursor/skills/**`) exists for a skill
- **AND** `~/.cursor/skills/<name>` is absent
- **WHEN** global Cursor sync presence is evaluated
- **THEN** `projection_present` SHALL be false
- **AND** project links SHALL remain out of scope for home projection ensure.

#### Scenario: External skill sync preview stays dry-run gated

- **WHEN** curated external install commands or projection ensure plans change
- **THEN** maintainers SHALL run `uv run wagents skills sync --dry-run`
- **AND** SHALL NOT run `uv run wagents skills sync --apply`, live
  `npx skills add ...`, or mass home symlink writes unless the maintainer
  explicitly requests live installation after Wave 2 review.
