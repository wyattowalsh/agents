# IDEAS Backlog Integration

## ADDED Requirements

### Requirement: Umbrella program tracks the full backlog with wave gates

The repository SHALL track the local research backlog's implementation as a
single wave-gated OpenSpec change (`integrate-ideas-backlog`) whose `tasks.md`
is the canonical, machine-checkable status source for every backlog item,
rather than allowing items to be implemented ad hoc without lane ownership or
a recorded validation bar.

#### Scenario: Every backlog item has a task ID and wave assignment

- **GIVEN** an item exists in the local research backlog's `MCP.md`,
  `DOCS.md`, `WORKFLOWS.md`, `AGENTS.md`, `SKILLS.md`, `CLI.md`, `TESTING.md`,
  or `INFRA.md`
- **WHEN** the program's `tasks.md` is inspected
- **THEN** the item maps to at least one task ID with an explicit wave
  (`W0`–`W15`) and status (`done`, `SKIP` with evidence, or `pending`)

### Requirement: Serial owners prevent collisions on shared generated surfaces

Any wave that edits a serialized shared surface MUST route through that
surface's single named owner recorded in `design.md`
(`SA-CI` for `.github/workflows/ci.yml`, `SA-DOC` for `wagents/docs.py`,
`SA-MCP0` for `config/mcp-registry.json`). A wave MUST NOT edit `ci.yml`
while a concurrent in-flight change holds an uncommitted diff to that file.

#### Scenario: CI gate additions are deferred when ci.yml has an uncommitted diff

- **GIVEN** `git diff --stat .github/workflows/ci.yml` reports a non-empty
  diff from a different, concurrently in-flight OpenSpec change
- **WHEN** this program's W1 quick-wins wave executes
- **THEN** the program records the exact intended `ci.yml` diff in `design.md`
  instead of applying it, and marks the corresponding task `blocked` (not
  `done`) in `tasks.md`

### Requirement: New MCP servers reuse the shared read-only library

Every MCP server introduced by this program MUST depend on the shared
read-only library for path-prefix allowlisting and catalog reads
(`wagents/mcp_shared/read_only_paths.py` for path-prefix allowlisting,
`wagents/mcp_shared/catalog_readers.py` for skill/agent catalog reads)
rather than each server re-implementing its own path guard or catalog
parser.

#### Scenario: A new MCP server rejects a path outside its allowlist

- **GIVEN** a W4/W10/W13 MCP server backed by `wagents/mcp_shared/read_only_paths.py`
- **WHEN** a tool call requests a path outside the server's configured
  allowlist prefixes
- **THEN** the server returns a structured error and does not read the file

### Requirement: Structural eval and hook gates run before merge

Structural eval and hook validation MUST run in the CI `validate` job and
MUST fail that job on a non-zero exit code once wired in (commands:
`wagents eval validate`, `wagents eval adequacy --strict`,
`wagents hooks validate --harness all`). Live LLM eval execution MUST NOT
run on every pull request; it stays behind `workflow_dispatch` or a nightly
schedule.

#### Scenario: A malformed eval file fails the validate job

- **GIVEN** a skill's `evals/*.json` file has invalid JSON or a missing
  required field
- **WHEN** the CI `validate` job runs `wagents eval validate --format json`
- **THEN** the job exits non-zero and the failure is visible in the job log
