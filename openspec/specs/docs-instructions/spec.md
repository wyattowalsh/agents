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
