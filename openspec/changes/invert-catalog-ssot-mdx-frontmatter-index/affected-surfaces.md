# Affected Surfaces

## Source Of Truth (Owned / Created By This Change)

- `openspec/changes/invert-catalog-ssot-mdx-frontmatter-index/` — this change-control set (proposal.md, design.md, affected-surfaces.md, validation-matrix.md, tasks.md).
- `config/schemas/skills-catalog-authoring.schema.json` — new frontmatter schema (skill_id, source_kind, install_*, trust_tier, provenance_*, notes, ...).
- `config/schemas/skills-catalog-index.schema.json` — new bundle index schema (version, generated_at, entries[] + body_path).
- `tests/test_skills_catalog_schemas.py` — minimal jsonschema/structural validation for the two new schemas.
- `docs/src/authoring/skills/external/` (dir + seed examples) — planned in W1+; referenced here.
- `docs/src/generated/` (or equivalent emitted index location) — generated bundle target (declared in docs-artifact-registry).

## Consuming / Retargeted Surfaces (Updated In Follow-On Waves)

- `wagents/external_skills.py` — read_external_skill_entries, dual-read (bundle → legacy parse), ExternalSkillEntry population.
- `wagents/catalog_rows.py` — curated_entry_by_name, entry_to_public_row, merge_installed_agents (retarget data sources).
- `wagents/docs/generate.py` + `wagents/docs/research.py` — emission of index from authoring MDX + catalog MDX regen.
- `wagents/validate.py` — quarantine / external skill checks retarget or extend to authoring sources.
- `wagents/site_model.py` — _source_kind, catalog node construction for external.
- `config/docs-artifact-registry.json` — declare new authoring source + generated index artifact.
- `config/sync-manifest.json` — ensure authoring/ and generated index are tracked for sync/drift.
- `AGENTS.md` §2.7 (and instructions/global.md, .github/copilot-instructions.md) — update curation workflow to "edit authoring MDX".
- `CONTRIBUTING.md` — external skill curation instructions.
- `scripts/` pre-commit / parity / drift checkers that reference external-skills.md parsing.

## Complementary / Observed Only (Not Owned)

- `config/external-skills.md` — legacy projection / fallback source during dual-read window (will be archived or emitted later).
- `docs/src/content/docs/skills/catalog/external/*.mdx` — still generated output (no hand edits).
- `skills/` custom skill trees — unchanged (their SKILL.md frontmatter remains separate).
- `wagents/parsing.py` (parse_frontmatter) — reused for MDX YAML frontmatter.
- Harness surface / mcp / hook registries — out of scope for Phase 1 (stay under config/).

## Tests

- New: `tests/test_skills_catalog_schemas.py`.
- Updated (later waves): `tests/test_external_skills.py`, `tests/test_docs.py`, `tests/test_site_model.py`, `tests/test_validate*.py`, catalog parity tests.
- `tests/test_skills_no_wagents.py` — ensure no cross-boundary issues if portable pieces added.

## Generated / Transient

- `generated-registries.json` (committed machine bundle).
- Regenerated catalog pages + README via `wagents docs generate` + `wagents readme`.
- One-time migration artifacts (if any scripts emit staging files).

## Validation Commands

- See `validation-matrix.md` (W0 scaffolding commands + W7 full matrix from plan).
- `uv run wagents openspec validate`
- `uv run pytest tests/test_skills_catalog_schemas.py -q`
- Later: `uv run wagents docs generate --no-installed`, `uv run wagents skills sync --dry-run`, full validate + build.
