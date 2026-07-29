# Delta: Deterministic Docs Graph And Harness Taxonomy

## ADDED Requirements

### Requirement: Docs graph validation is pure and date-deterministic

Docs graph/report computation and validation SHALL be pure with respect to
filesystem mutation and wall-clock access. Mutation internals SHALL receive one
explicit UTC snapshot date in `YYYY-MM-DD` form. The docs CLI MAY accept
optional `--snapshot-date`; when omitted in mutation mode, the CLI/generator
boundary SHALL capture the current UTC date exactly once and pass it explicitly
through all related report writers.

#### Scenario: Check mode validates generated reports

- **WHEN** docs graph check or stale validation runs
- **THEN** it SHALL read no wall clock
- **AND** it SHALL write no report, manifest, history row, or generated page.

#### Scenario: Explicit snapshot date is supplied

- **WHEN** mutation runs with `--snapshot-date 2026-07-29`
- **THEN** every related graph/report history entry SHALL use `2026-07-29`
- **AND** equal source inputs plus that date SHALL produce byte-identical output.

#### Scenario: Mutation option is omitted

- **WHEN** an established docs-generation caller omits `--snapshot-date`
- **THEN** the CLI/generator boundary SHALL capture the current UTC date once
- **AND** all mutation internals SHALL receive that same explicit date
- **AND** validation/check paths SHALL still perform no clock read.

#### Scenario: Supplied snapshot date is invalid

- **WHEN** a caller supplies a value that is not a valid UTC calendar date in
  `YYYY-MM-DD` form
- **THEN** mutation SHALL fail before any write.

### Requirement: Public harness taxonomy preserves three surface classes

Public docs data SHALL define the managed harness set as exactly
`claude-code`, `codex`, `crush`, `cursor`, `grok`, and `opencode`; the Skills
CLI-native set as exactly `claude-code`, `codex`, `crush`, `cursor`, and
`opencode`; and MCP-only/hybrid clients as separately typed surfaces excluded
from both counts.

#### Scenario: Homepage support data is generated

- **WHEN** homepage rows and counts are projected
- **THEN** each managed harness SHALL appear exactly once in the managed set
- **AND** the managed count SHALL be six
- **AND** the Skills CLI-native count SHALL be five
- **AND** MCP-only/hybrid rows SHALL carry their own surface kind without
  changing either count.

#### Scenario: README support grouping is generated

- **WHEN** `wagents readme` renders support information
- **THEN** the six managed harnesses SHALL be grouped as managed
- **AND** MCP-only/hybrid clients SHALL be grouped or labeled separately
- **AND** README identities and counts SHALL agree with homepage/site data.
