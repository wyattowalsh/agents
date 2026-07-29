# Delta: Portable Skill Manifest Enrichment

## ADDED Requirements

### Requirement: Manifest enrichment uses real YAML semantics

The portable skill-package manifest enricher SHALL parse `SKILL.md`
frontmatter with a real YAML safe loader. Folded and literal scalars, chomping,
quoted values, lists, mappings, and malformed YAML SHALL follow YAML semantics
rather than line-oriented string stripping.

#### Scenario: Description uses a folded scalar

- **WHEN** `SKILL.md` declares `description: >` or another folded-scalar form
- **THEN** the enriched description SHALL equal the YAML-decoded value
- **AND** scalar indicators or indentation SHALL NOT leak into the manifest.

#### Scenario: Frontmatter YAML is malformed

- **WHEN** the YAML safe loader rejects the frontmatter
- **THEN** enrichment SHALL fail before writing
- **AND** an existing enriched manifest SHALL remain unchanged.

### Requirement: Harness targets derive from portable metadata

The enricher SHALL derive harness targets from supplied portable catalog or
sync metadata. Output SHALL record target-source status, selected source, and
source content digest. It SHALL NOT substitute a hardcoded target list.

#### Scenario: Catalog metadata is supplied

- **WHEN** portable catalog metadata contains the selected skill and target set
- **THEN** the enricher SHALL derive targets from that row
- **AND** output SHALL bind the catalog source and its content digest.

#### Scenario: Only sync metadata is supplied

- **WHEN** no applicable catalog row exists and portable sync metadata supplies
  the selected skill's target set
- **THEN** the enricher SHALL derive targets from sync metadata
- **AND** output SHALL bind the sync source and its content digest.

#### Scenario: No portable target metadata is available

- **WHEN** neither applicable catalog nor sync metadata is supplied
- **THEN** output SHALL report target-source status as unavailable
- **AND** the derived target set SHALL be empty
- **AND** no repository-supported target list SHALL be guessed.

### Requirement: Installed enrichment stays repository-independent

The installed skill-package manifest enricher SHALL NOT import the repository
`wagents` package and SHALL keep preview/dry-run non-mutating. Any YAML runtime
dependency SHALL be declared by the portable skill compatibility contract.

#### Scenario: Enricher runs from an installed skill package

- **WHEN** the script executes without the repository application package on
  `PYTHONPATH`
- **THEN** parsing and preview SHALL work using only declared portable
  dependencies and explicit metadata inputs
- **AND** no `wagents` import or machine-local absolute path SHALL be required.

#### Scenario: Apply was not requested

- **WHEN** preview or `--dry-run` executes without explicit `--apply`
- **THEN** no enriched manifest file SHALL be created or modified.
