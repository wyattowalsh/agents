# Downstream Tooling Delta

## Purpose

Define how Chrome DevTools MCP source ownership is represented across downstream harnesses so plugin, extension, repo MCP, and manual UI integrations do not collide.

## ADDED Requirements

### Requirement: Chrome DevTools Source Ownership Is Singular Per Harness

Each supported harness SHALL have at most one active `chrome-devtools` MCP owner.

#### Scenario: Harness uses upstream plugin ownership

- **WHEN** a harness is marked as using the upstream Chrome DevTools plugin
- **THEN** repo sync SHALL NOT also project an active standalone `chrome-devtools` MCP entry into that harness
- **AND** the registry SHALL identify the source as `plugin`.

#### Scenario: Harness uses upstream extension ownership

- **WHEN** a harness is marked as using the upstream Chrome DevTools extension
- **THEN** repo sync SHALL NOT also project an active standalone `chrome-devtools` MCP entry into that harness
- **AND** the registry SHALL identify the source as `extension`.

#### Scenario: Harness lacks verified plugin support

- **WHEN** no concrete plugin or extension surface has been verified for a harness
- **THEN** the harness SHALL use `repo-mcp`, `manual-ui`, or `blind-spot` status
- **AND** documentation SHALL avoid claiming native plugin installation support.

### Requirement: Imported Chrome DevTools Skills Preserve Provenance

Imported Chrome DevTools skills SHALL retain clear provenance and local adaptation notes.

#### Scenario: A Chrome DevTools skill is promoted into `skills/`

- **WHEN** a skill derived from `ChromeDevTools/chrome-devtools-mcp` is added to the repository
- **THEN** its frontmatter SHALL include `license: Apache-2.0`
- **AND** its metadata SHALL identify `Google LLC` as upstream author and `0.23.0` as upstream package version
- **AND** its body or references SHALL include source URL, commit SHA, access date, and adaptation notes.

### Requirement: Chrome DevTools Runtime Artifacts Stay Out Of Version Control

Chrome DevTools workflows SHALL warn users away from committing runtime artifacts.

#### Scenario: A skill describes traces, screenshots, Lighthouse reports, heap snapshots, or browser profiles

- **WHEN** a promoted Chrome DevTools skill instructs the user to generate browser debugging artifacts
- **THEN** it SHALL include guidance to keep those artifacts local unless the user explicitly asks to save or share them
- **AND** generated runtime artifact paths SHALL NOT be added to committed source by default.
