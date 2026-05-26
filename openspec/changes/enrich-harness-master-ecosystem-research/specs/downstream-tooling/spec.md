# Downstream Tooling Delta

## MODIFIED Requirements

### Requirement: Harness Master Audits Are Evidence-Gated

The repository SHALL keep `harness-master` dry-run first for harness audits and SHALL require explicit approval before any config, install, plugin, extension, MCP, or skill apply step.

#### Scenario: Researching ecosystem improvements

- **WHEN** a user invokes `harness-master` with `research <harness|all> <config|plugin|extension|mcp|skill|all> [goal]`
- **THEN** the skill SHALL plan read-only source access before recommending candidates
- **AND** the report SHALL distinguish official, local-registry, package-registry, GitHub, MCP-registry, skill-hub, security, and community evidence
- **AND** the workflow SHALL stop before edits, installs, or generated docs changes.

#### Scenario: Scoring candidate adoption

- **WHEN** a user invokes `candidate <source-or-url> <harness|all> [level]` or `compare <candidate...> for <harness|all>`
- **THEN** the skill SHALL normalize evidence into candidate dossiers
- **AND** score authority, programmatic evidence, harness fit, overlap/DRY, install friction, maintenance, popularity, security, permissions/auth risk, validation path, and rollback path
- **AND** map the result to one of `validated`, `repo-present-validation-required`, `planned-research-backed`, `experimental`, or `quarantine` support tiers.

#### Scenario: Credentialed source is unavailable

- **GIVEN** a source requires an optional credential
- **WHEN** the required environment variable is missing
- **THEN** source planning SHALL mark the source as degraded instead of failing
- **AND** confidence SHALL be lowered unless corroborating non-credentialed evidence exists.

#### Scenario: Community praise is the only evidence

- **WHEN** social, forum, blog, or community sentiment is the only positive signal for a candidate
- **THEN** the skill SHALL refuse adoption or apply recommendations
- **AND** may only recommend further inspection with official or machine-readable corroboration required.

#### Scenario: GitHub enrichment follows discovery

- **WHEN** GitHub is used for ecosystem research
- **THEN** REST search and code/file lookup SHALL be treated as broad discovery mechanisms
- **AND** GraphQL SHALL be treated as a batched enrichment layer for known candidate repositories, not a full replacement for discovery.
