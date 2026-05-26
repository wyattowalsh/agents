# Agent Assets Delta

## MODIFIED Requirements

### Requirement: Asset Formats Stay Canonical

The repository SHALL keep skill, agent, MCP, instruction, hook, and bundle metadata formats documented in `AGENTS.md` and validated by `wagents` commands.

#### Scenario: Adding a preference-driven project initialization skill

- **WHEN** the `new-project` skill is added under `skills/new-project/SKILL.md`
- **THEN** its frontmatter `name` SHALL match the directory name
- **AND** the skill SHALL keep the main body as a dispatch, safety, reference, script, and validation contract
- **AND** detailed stack preferences SHALL live in typed data, references, scripts, and templates rather than only in prose.

#### Scenario: Validating project initialization catalogs

- **WHEN** a skill stores machine-readable capability and preset catalogs under `skills/new-project/data/`
- **THEN** repository validation SHALL include a catalog validation command
- **AND** missing capability dependencies, preset references, and unsafe external-side-effect metadata SHALL be reported before completion.

#### Scenario: Guarding scaffold side effects

- **WHEN** a project initialization workflow proposes file mutation, package installs, cloud operations, deploys, DNS, releases, Docker, or external account changes
- **THEN** the workflow SHALL produce a blueprint before mutation
- **AND** each external side-effect or destructive-risk category SHALL require explicit approval.
