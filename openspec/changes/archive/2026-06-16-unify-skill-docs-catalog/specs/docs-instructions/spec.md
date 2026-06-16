# docs-instructions Delta

## ADDED Requirements

### Requirement: Unified skill catalog detail URLs

Generated skill documentation SHALL publish one detail page per skill at `/skills/catalog/<name>/` and compile hub indexes from the same deduped node list.

#### Scenario: Docs generate emits catalog detail pages

- **WHEN** `wagents docs generate` runs
- **THEN** each skill node writes `docs/src/content/docs/skills/catalog/<id>.mdx`
- **AND** hub pages `skills/index.mdx`, `skills/all.mdx`, and `skills/install.mdx` are generated without importing a JSON `SkillCatalog` component.

### Requirement: Legacy skill URLs redirect to catalog

The docs site SHALL redirect legacy `/skills/<name>/` detail URLs to `/skills/catalog/<name>/` with HTTP 308, excluding hub slugs.

#### Scenario: Legacy detail URL is requested

- **WHEN** a client requests `/skills/honest-review/`
- **THEN** middleware responds with 308 to `/skills/catalog/honest-review/`.

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
