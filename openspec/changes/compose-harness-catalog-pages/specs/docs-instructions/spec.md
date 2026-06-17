## ADDED Requirements

### Requirement: Composed catalog pages use standardized frontmatter

Generated and composed catalog pages SHALL emit `page_kind`, `source_kind`, `asset_id`, `composed`, and `docs_density: standard` in Starlight frontmatter.

#### Scenario: Generator scaffolds skill page

- **WHEN** `wagents docs generate` writes a skill catalog page
- **THEN** frontmatter includes the standardized catalog contract fields
- **AND** `docs_density` is `standard` by default

### Requirement: Composed pages are preserved on regenerate

Pages marked `composed: true` or containing `HAND-MAINTAINED` SHALL be skipped by `wagents docs generate`.

#### Scenario: Composed page exists

- **GIVEN** a catalog MDX file with `composed: true`
- **WHEN** `wagents docs generate` runs
- **THEN** the file is preserved unchanged

### Requirement: Compose wave emission

`wagents docs compose --emit-waves` SHALL emit orchestrator-consumable batch prompts for pending catalog pages.

#### Scenario: Emit custom skill compose wave

- **WHEN** `wagents docs compose --emit-waves --surface skills --dry-run`
- **THEN** batch prompts list target paths, source assets, and composition instructions
