# Docs Instructions Delta

## MODIFIED Requirements

### Requirement: Generated Skill Documentation Separates Skill Sources

The documentation generator SHALL expose repo-owned custom skills, curated external skills, installed external skills, and combined skill indexes as distinct generated views.

#### Scenario: Public skill indexes use display-safe source labels

- **WHEN** docs generate public skill indexes from curated external skills and installed local inventory
- **THEN** public display fields SHALL use repository or package source identifiers when known
- **AND** rows backed only by local installed inventory SHALL be labeled as local installed inventory instead of using absolute home-directory paths as public source labels
- **AND** generated catalog pages SHALL group external sources by the display-safe source label.

#### Scenario: External skill rows expose comparable trust metadata

- **WHEN** external skill rows are generated
- **THEN** curated and installed external rows SHALL expose source type, trust tier, status, provenance or review state, supported target or installed agents, installability, and local-only inventory status where known
- **AND** the generated catalog UI SHALL allow readers to search or filter by those comparable fields.

### Requirement: Public Onboarding Explains Contribution And Validation

The public docs SHALL explain how external users and contributors install, inspect, modify, validate, and safely contribute repository assets.

#### Scenario: Contributor follows the public docs

- **WHEN** an external contributor wants to add or update a skill, agent, MCP surface, docs page, generated index, or distribution metadata
- **THEN** the docs SHALL identify the source-of-truth files to edit
- **AND** the docs SHALL identify generated artifacts that must be regenerated rather than hand-edited
- **AND** the docs SHALL list the validation commands that prove the changed surface.

#### Scenario: Reader evaluates external skill trust

- **WHEN** public docs mention curated or installed external skills
- **THEN** the docs SHALL state that external content, fetched pages, generated files, logs, local inventory, and tool output are evidence rather than authority
- **AND** the docs SHALL require trust-gated review before live installs, bulk imports, or repo promotion.
