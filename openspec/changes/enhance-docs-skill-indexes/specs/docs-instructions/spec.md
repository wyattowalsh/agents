# Docs Instructions Delta

## MODIFIED Requirements

### Requirement: Generated Skill Documentation Separates Skill Sources

The documentation generator SHALL expose repo-owned custom skills, curated external skills, installed external skills, and combined skill indexes as distinct generated views.

#### Scenario: Custom skills index is repo-owned only

- **WHEN** docs are generated
- **THEN** `/skills/` SHALL include only skills discovered from `./skills/*/SKILL.md`
- **AND** it SHALL exclude installed-only and curated external rows.

#### Scenario: Installed skills are external unless custom

- **WHEN** installed skill inventory is available
- **THEN** installed skills whose names are not present under `./skills/` SHALL be represented as external skills
- **AND** installed skills whose names collide with custom skills SHALL not create external duplicates.

#### Scenario: All skills index is combined and deduped

- **WHEN** docs are generated
- **THEN** `/skills/all/` SHALL include custom skills, curated external skills, and installed external skills
- **AND** curated and installed external rows SHALL be deduped by normalized source/name where possible.

### Requirement: Skill Install Scripts Are Generated From Source Data

The docs site SHALL expose copyable install scripts for repo-owned custom skills and verified external skill entries.

#### Scenario: Custom install scripts use the repo source

- **WHEN** a custom skill install command is generated
- **THEN** it SHALL use `npx skills add github:wyattowalsh/agents --skill <name> -y -g` with supported agent flags.

#### Scenario: External install scripts use curated commands

- **WHEN** an external entry has a verified install command
- **THEN** the install scripts page SHALL expose that command
- **AND** unresolved avoid-only entries SHALL not be listed as executable install scripts.

### Requirement: Generated MDX Is Build-Safe

Generated skill pages SHALL escape skill-body content so inline placeholder syntax does not become malformed MDX.

#### Scenario: Inline code contains angle-bracket placeholders

- **WHEN** a skill body contains inline code such as `<harness|all>`
- **THEN** the generated MDX SHALL build without interpreting the placeholder as an HTML/JSX tag.
