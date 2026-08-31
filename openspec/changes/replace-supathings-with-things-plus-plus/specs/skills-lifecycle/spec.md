# Skills Lifecycle Spec Delta — Things Manager v2

## ADDED Requirements

### Requirement: Things Manager v2 is the portable semantic and safety layer

`skills/things-manager` SHALL release as version `2.0.0`, remove active SupaThings/tool-name assumptions, route through the Things++ capability matrix, and remain packaged only by the repository root plugin.

#### Scenario: Portable and native skill metadata are reconciled

- **WHEN** the portable v2 skill stabilizes
- **THEN** root frontmatter SHALL contain only portable fields
- **AND** `argument-hint` or other native-only metadata SHALL remain in `config/skill-adapters.json`
- **AND** no nested Things plugin or copied skill tree SHALL be created.

### Requirement: Things Manager preserves all 17 workflows and safety invariants

The skill SHALL preserve the 17 canonical workflows and enforce read-before-write, ID-first targeting, duplicate prevention, ambiguity blocking, default maximum batch 25, preview/confirmation, cross-backend serialization, read-after-write verification, privacy, and changed/skipped/failed/ambiguous reporting. It SHALL classify `create_structured_project`, `edit_items`, and `duplicate_items` as bulk writes, identify `edit_items` as non-undoable, require affected-child counts for heading/area deletion previews, treat Quick Entry as a UI handoff, and reject tag-parent detach in v1.

#### Scenario: A backend gap or unsupported request occurs

- **WHEN** a required fixed bridge is unavailable or the request is recurrence editing, deterministic reorder, or arbitrary/raw execution
- **THEN** the skill SHALL report the unavailable/unsupported capability and safe next action
- **AND** SHALL NOT silently switch to an unapproved backend or claim success.

### Requirement: Things Manager has a 41-case v2 eval corpus

The skill eval manifest SHALL contain exactly 41 unique cases: rewritten equivalents of all 25 legacy concepts plus 16 additive Things++ routing, coverage, degradation, concurrency, unsupported, destructive, and prompt-injection cases.

#### Scenario: Eval coverage is validated

- **WHEN** eval validate, coverage, and strict adequacy run
- **THEN** every legacy concept and all 17 workflows SHALL have an explicit case mapping
- **AND** the additive cases SHALL cover sole-group parity, exact 70 closure, core precedence, fixed native/Shortcut selection, unavailable bridges, cross-backend serialization, stale-write verification, max-25 create, no-raw structured creation, destructive administration, recurrence/reorder refusal, and untrusted content.

### Requirement: Capability copies are generated from one skill-owned ledger

`skills/things-manager/references/capabilities.md` SHALL be the canonical human-readable routing ledger, with deterministic maintainer and ChatGPT projections and a `--check` parity mode.

#### Scenario: A capability contract changes

- **WHEN** a tool, workflow route, scope, safety class, or unsupported capability changes
- **THEN** maintainers SHALL update the canonical ledger and run its generator
- **AND** parity check SHALL fail if generated copies drift or claim a capability not present in the 70-tool manifest.

### Requirement: The capability manifest freezes exact skill coverage IDs

The active change SHALL enumerate every one of the 70 tools, 37 Supa outcomes, 17 workflow IDs, 25 legacy eval IDs, and 16 additive eval IDs in schema-validated machine-readable form.

#### Scenario: Coverage or an eval inventory changes

- **WHEN** an implementation adds, removes, renames, or remaps any enumerated row
- **THEN** the active OpenSpec and manifest SHALL be revised before source generation
- **AND** semantic validation SHALL require zero removed/unmapped rows and net-new outcomes greater than zero.
