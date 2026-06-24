# docs-instructions Specification

## Purpose
Define documentation and instruction-sync requirements for keeping generated docs, platform bridge files, and source instructions aligned.
## Requirements
### Requirement: Generated docs and instruction truth

The docs/instructions lane SHALL consolidate README, docs, support matrices, and AI instructions from registries and fragments after schema freeze.

#### Scenario: Child lane updates a support fragment

- **GIVEN** a child lane changes a manifest or fragment
- **WHEN** docs consolidation runs
- **THEN** generated docs reflect the fragment without child teams editing global docs directly.

### Requirement: Support matrices preserve surface distinctions

Generated support matrices SHALL distinguish desktop, web/cloud, CLI, editor, and experimental harness variants instead of collapsing products into one row.

#### Scenario: Harness family has multiple variants

- **GIVEN** a registry contains related harness variants such as Claude Code and Claude Desktop
- **WHEN** C08 generates support documentation
- **THEN** each variant is rendered with its own support tier, owner lane, and validation status.

### Requirement: Blind spots are labeled

Docs SHALL label unsupported, unverified, experimental, and quarantine surfaces rather than omitting them or implying support.

#### Scenario: Surface lacks validation evidence

- **GIVEN** a harness or external asset exists in planning but lacks validation evidence
- **WHEN** docs mention that surface
- **THEN** the docs render the correct blind-spot label and next validation owner.

### Requirement: Generated outputs require scheduled consolidation

Generated docs, root README updates, and bridge instruction files SHALL only be refreshed when C08 has stable inputs and an explicitly scheduled generated-output pass.

#### Scenario: Shared docs are dirty from another lane

- **GIVEN** generated docs or root instruction files are dirty outside C08 ownership
- **WHEN** C08 defines docs truth contracts
- **THEN** C08 records the blocker and commits source fragments without overwriting shared generated outputs.

### Requirement: Grouped skill catalog detail URLs

Generated skill documentation SHALL publish one detail page per skill under `/skills/catalog/custom/<name>/` (repo-owned) or `/skills/catalog/external/<name>/` (curated-external and optional installed inventory) and compile hub indexes from the same deduped node list.

#### Scenario: Docs generate emits catalog detail pages

- **WHEN** `wagents docs generate` runs
- **THEN** each custom skill node writes `docs/src/content/docs/skills/catalog/custom/<id>.mdx`
- **AND** each external skill node writes `docs/src/content/docs/skills/catalog/external/<id>.mdx`
- **AND** hub pages `skills/catalog/index.mdx`, `skills/catalog/custom/index.mdx`, `skills/catalog/external/index.mdx`, and `skills/install.mdx` are generated without importing a JSON `SkillCatalog` component
- **AND** the Starlight sidebar autogenerates `skills/catalog/custom` and `skills/catalog/external` detail trees.

#### Scenario: Public docs default omits installed-only externals

- **WHEN** `wagents docs generate --no-installed` runs
- **THEN** curated-external catalog rows are emitted under `skills/catalog/external/`
- **AND** harness-installed-only skills are omitted unless `--include-installed` is set.

### Requirement: Canonical catalog URLs only

The docs site SHALL serve skill detail pages only at grouped catalog paths. Legacy flat hubs (`/skills/`, `/skills/all/`) and flat detail URLs (`/skills/catalog/<name>/`, `/skills/<name>/`) SHALL NOT be generated or redirected.

#### Scenario: Catalog landing links to grouped indexes

- **WHEN** a reader opens `/skills/catalog/`
- **THEN** the page links to `/skills/catalog/custom/` and `/skills/catalog/external/` rather than a combined all-skills hub.

### Requirement: Sync desired set includes repo and Install Now curated skills

`wagents skills sync` SHALL treat repo-owned skills and Install Now curated external skills as desired even when they are not yet present in harness inventory.

#### Scenario: Uninstalled Install Now skill is missing for a target harness

- **GIVEN** a curated Install Now entry targets `codex`
- **AND** the skill is absent from the installed inventory snapshot
- **WHEN** `wagents skills sync --agent codex` runs
- **THEN** the skill appears in the missing list with a verified install command.

### Requirement: Cached skill research is optional evidence

When per-skill research artifacts exist under `docs/src/skill-research/<name>.md`, generated docs pages SHALL embed them as evidence with an explicit non-authority disclaimer.

#### Scenario: Phase A research is seeded from repository skills

- **WHEN** `wagents docs research --seed-from-repo --source-type custom --no-installed` runs
- **THEN** each repo-owned custom skill receives a validated research artifact grounded in `skills/<name>/SKILL.md`
- **AND** `wagents docs research --check-research --source-type custom --no-installed` exits 0 when coverage is complete.

### Requirement: Catalog Authoring MDX Is Human SSOT For Bucket A Skills

The repository SHALL treat per-skill authoring files under `docs/src/authoring/skills/*.mdx` as the human-editable source of truth for catalog semantics (custom and curated-external skills). Each authoring file SHALL carry structured YAML frontmatter including `name`, `description`, and `source_kind` (`custom`, `curated-external`, or `external`), plus optional curated fields (`install_command`, `install_source`, `trust_tier`, `status`, `target_agents`, provenance and risk notes). Authoring rows that use either accepted external skill source kind SHALL produce the same generated external catalog metadata behavior.

#### Scenario: Maintainer edits a curated external skill

- **WHEN** a maintainer updates a curated external skill entry
- **THEN** they SHALL edit the corresponding `docs/src/authoring/skills/<id>.mdx` frontmatter and body
- **AND** they SHALL NOT hand-edit generated catalog pages under `docs/src/content/docs/skills/catalog/`.

#### Scenario: Repo-owned custom skills project from SKILL.md

- **WHEN** a repo-owned skill under `skills/<name>/SKILL.md` changes
- **THEN** `wagents docs generate` (or `wagents catalog sync-authoring`) SHALL project or refresh the matching authoring MDX with `source_kind: custom`
- **AND** the authoring body SHALL reference the SKILL.md source via a generated marker comment.

#### Scenario: Curated external audit metadata is authored

- **WHEN** a curated external entry is promoted, demoted, or retained after review
- **THEN** its authoring MDX MAY include structured audit fields for license, license status, audit date, audited head, pin policy, no-pin rationale, source-list evidence, executable surface, allowed tools, hook surface, script surface, credential behavior, network access, file access, live-action risk, risk category, dedupe notes, and unsupported target agents
- **AND** generated catalog index rows SHALL preserve those fields for docs, validation, and sync review consumers.

#### Scenario: External skill authoring source kinds are accepted

- **WHEN** an authoring MDX row uses `source_kind: curated-external` or `source_kind: external`
- **THEN** generated catalog indexes and detail-page nodes SHALL classify the row as an external catalog entry
- **AND** SHALL preserve the row's install, target-agent, provenance, audit, risk, dedupe, and unsupported-target metadata for downstream docs, validation, and sync consumers.

#### Scenario: Curated external evidence gaps are reported

- **WHEN** maintainers run `uv run wagents catalog audit`
- **THEN** the command SHALL read generated catalog data without mutating source files
- **AND** SHALL report external row counts, status counts, missing audit field counts, issue-code counts, and per-row issues in text, JSON, or JSONL.
- **AND** the command SHALL exit zero by default so evidence debt can be measured before strict gates are enabled.
- **AND** `--strict` SHALL exit nonzero when warning or error audit issues are present.

#### Scenario: Skill or catalog docs change

- **WHEN** source changes affect skill definitions, catalog schema, public docs, generated docs behavior, or instruction surfaces
- **THEN** the maintainer SHALL invoke `docs-steward` when available after source regeneration/build validation
- **AND** SHALL record the docs-steward finding or blocker when it is not available.

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

