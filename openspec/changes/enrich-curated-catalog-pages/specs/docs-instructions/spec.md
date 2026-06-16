# Docs Instructions Delta

## MODIFIED Requirements

### Requirement: Cached skill research is optional evidence

When per-skill research artifacts exist under `docs/src/skill-research/<name>.md`, generated docs pages SHALL embed them as evidence with an explicit non-authority disclaimer. Research artifacts are supported for `custom`, `curated-external`, and (optionally) `installed` source types.

#### Scenario: Phase A research seeded for repo-owned custom skills

- **WHEN** `wagents docs research --seed-from-repo --source-type custom --no-installed` runs
- **THEN** each repo-owned custom skill receives a validated research artifact grounded in `skills/<name>/SKILL.md`
- **AND** `wagents docs research --check-research --source-type custom --no-installed` exits 0 when coverage is complete.

#### Scenario: Curated-external catalog pages support research enrichment

- **WHEN** a curated-external skill node (from Install Now entries in `config/external-skills.md`) has a research artifact under `docs/src/skill-research/<name>.md`
- **THEN** the generated catalog detail page at `/skills/catalog/<name>/` SHALL embed the research brief
- **AND** the page SHALL continue to render harness rows, trust tier, install command, provenance, and source label from curated metadata
- **AND** the embedding SHALL use the same evidence disclaimer as custom skills.

#### Scenario: Research emission supports wave orchestration (emit-waves)

- **WHEN** `wagents docs research --emit-waves --source-type curated-external --dry-run` (or equivalent) is invoked
- **THEN** structured batch prompts suitable for subagent waves (orchestrator) SHALL be emitted
- **AND** no research artifacts are written unless the consumer explicitly writes them
- **AND** the emission respects `--batch-size` and source filters.

### Requirement: Unified skill catalog detail URLs and parity

Generated skill documentation SHALL publish one detail page per skill at `/skills/catalog/<name>/` (including curated-external stubs and enriched pages) and the catalog SHALL maintain ID parity with the desired sync set (repo-owned + Install Now curated entries from `external-skills.md`).

#### Scenario: Curated Install Now skills appear in catalog with parity to sync

- **WHEN** `wagents docs generate --no-installed` runs (CI default)
- **THEN** every Install Now curated skill ID from `config/external-skills.md` SHALL produce (or link to) a catalog page under `/skills/catalog/`
- **AND** `wagents skills sync --dry-run` for supported targets SHALL report the same IDs as desired (missing or already-present) without drift.

#### Scenario: Enriched curated pages remain CI-safe

- **WHEN** docs generate runs without network or installed inventory
- **THEN** curated catalog pages render using cached research (if present) or stub metadata; lazy upstream previews (on-demand fetch) are not required for the build to succeed.

## ADDED Requirements (if extending base spec)

### Requirement: Public catalog distinguishes enriched vs stub curated entries

Generated public catalog views and indexes SHALL indicate when a curated-external entry is backed by a research artifact (evidence tier) vs pure stub, without implying full upstream content is vendored.

#### Scenario: Reader sees enrichment status

- **WHEN** viewing a `/skills/catalog/<curated-name>/` or hub row for curated-external
- **THEN** presence of research artifact SHALL be reflected (e.g., "research brief available" or embedded content) with clear "evidence, not authority" labeling
- **AND** install command and harness compatibility remain primary actionable content.