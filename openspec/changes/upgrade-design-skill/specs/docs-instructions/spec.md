# Docs Instructions Delta

## MODIFIED Requirements

### Requirement: Cached skill research is optional evidence

When per-skill research artifacts exist under `docs/src/skill-research/<name>.md`, generated docs pages SHALL embed them as evidence with an explicit non-authority disclaimer.

#### Scenario: Design research documents external UI ecosystem evidence

- **WHEN** the `design` skill upgrade is implemented
- **THEN** `docs/src/skill-research/design.md` SHALL document the external UI/design/taste sources reviewed
- **AND** it SHALL include trust, install, hook, credential, network, overlap, accepted-pattern, rejected-pattern, and implementation-target notes
- **AND** it SHALL include a fold/remove matrix for repo-owned Chrome DevTools wrapper skills and overlapping curated UI/design/frontend/browser-proof catalog rows
- **AND** generated docs SHALL publish the research page for `design`.

### Requirement: Catalog Authoring MDX Is Human SSOT For Bucket A Skills

The repository SHALL treat per-skill authoring files under `docs/src/authoring/skills/*.mdx` as the human-editable source of truth for catalog semantics (custom and curated-external skills). Each authoring file SHALL carry structured YAML frontmatter including `name`, `description`, and `source_kind` (`custom` or `curated-external`), plus optional curated fields (`install_command`, `install_source`, `trust_tier`, `status`, `target_agents`, provenance and risk notes).

#### Scenario: Custom design authoring replaces frontend-designer

- **WHEN** authoring sources are synced for repo-owned custom skills
- **THEN** `docs/src/authoring/skills/design.mdx` SHALL describe the custom `design` skill
- **AND** stale `docs/src/authoring/skills/frontend-designer.mdx` SHALL be removed unless an approved compatibility policy requires a documented redirect.

#### Scenario: Folded skill authoring rows are removed

- **WHEN** overlapping browser-proof and UI/design catalog rows are folded into `design`
- **THEN** active authoring rows for the folded custom Chrome DevTools wrapper skills SHALL be removed
- **AND** active authoring rows for folded curated external UI/design/frontend/browser-proof rows SHALL be removed after useful synthesis is captured in `docs/src/skill-research/design.md`
- **AND** generated catalog pages for folded rows SHALL be absent after docs generation.
