# Docs Instructions Delta

## ADDED Requirements

### Requirement: Catalog Authoring MDX Is Human SSOT For Bucket A Skills

The repository SHALL treat per-skill authoring files under `docs/src/authoring/skills/*.mdx` as the human-editable source of truth for catalog semantics (custom and curated-external skills). Each authoring file SHALL carry structured YAML frontmatter including `name`, `description`, and `source_kind` (`custom` or `curated-external`), plus optional curated fields (`install_command`, `install_source`, `trust_tier`, `status`, `target_agents`, provenance and risk notes).

#### Scenario: Maintainer edits a curated external skill

- **WHEN** a maintainer updates a curated external skill entry
- **THEN** they SHALL edit the corresponding `docs/src/authoring/skills/<id>.mdx` frontmatter and body
- **AND** they SHALL NOT hand-edit generated catalog pages under `docs/src/content/docs/skills/catalog/`.

#### Scenario: Repo-owned custom skills project from SKILL.md

- **WHEN** a repo-owned skill under `skills/<name>/SKILL.md` changes
- **THEN** `wagents docs generate` (or `wagents catalog sync-authoring`) SHALL project or refresh the matching authoring MDX with `source_kind: custom`
- **AND** the authoring body SHALL reference the SKILL.md source via a generated marker comment.

### Requirement: Committed Catalog Index Bundle Is Machine SSOT

`wagents docs generate` SHALL emit a committed machine bundle at `docs/public/generated-registries/skills-catalog-index.json` from authoring MDX frontmatter and body paths. Downstream consumers (`external_skills`, docs site model, validate quarantine, discover inventory) SHALL prefer this index when present.

#### Scenario: CI docs generate emits index

- **WHEN** `uv run wagents docs generate --no-installed` runs in CI
- **THEN** it SHALL write `skills-catalog-index.json` with versioned structure validated by `config/schemas/skills-catalog-index.schema.json`
- **AND** catalog MDX pages SHALL be regenerated from the index without changing public URL shapes.

#### Scenario: Dual-read fallback during migration

- **WHEN** the catalog index or authoring directory is absent or empty
- **THEN** consumers SHALL fall back to parsing `config/external-skills.md` via the legacy parser
- **AND** operators MAY force legacy reads with `WAGENTS_CATALOG_LEGACY_EXTERNAL_MD=1`.

### Requirement: External Skills Registry Projection Is Derived

`config/external-skills.md` SHALL be treated as a deprecated legacy projection during the Bucket A inversion. New curation work SHALL target authoring MDX; the flat markdown file MAY be regenerated from authoring for compatibility but SHALL NOT be the authoritative edit surface.

#### Scenario: Legacy projection remains parseable

- **WHEN** tooling reads curated external install commands before full cutover
- **THEN** `read_external_skill_entries()` SHALL return rows from the index or authoring sources first
- **AND** legacy markdown parsing SHALL remain available as a fallback until an explicit cutover change removes it.
