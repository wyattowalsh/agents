# Docs Instructions Delta

## MODIFIED Requirements

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
