# Proposal

## Problem

`config/external-skills.md` serves as the current canonical source for curated external skill install commands, provenance, trust tiers, and notes. At the same time, generated catalog pages and indexes under `docs/src/content/docs/skills/catalog/external/` (plus site model / catalog row builders) derive overlapping truth from the markdown parse plus research artifacts. This creates a dual-SSOT: edits must be coordinated in the flat MD + generated MDX surfaces, consumers (external_skills parser, docs generate, discover, validate, sync) read the config form, and catalog enrichment lives in docs. The result is drift risk, high coordination cost for per-skill changes, and blocked progress toward docs-authoring as the human-editable layer.

## Intent

Invert the SSOT for (initially external) catalog semantics to **per-skill authoring MDX files** carrying structured frontmatter (under `docs/src/authoring/skills/external/`) + a committed generated machine index (`generated-registries.json` or equivalent under docs generate). `config/external-skills.md` becomes a derived / legacy projection during migration (dual-read supported). Phase 1 scope is external-skills authoring only; other Bucket A registries (mcp, hooks, harness-surface) remain config-first for this change.

## Scope

- Create this OpenSpec change directory with proposal, design, affected-surfaces, validation-matrix (W7 commands), tasks (wave-mapped).
- Define `config/schemas/skills-catalog-authoring.schema.json` (frontmatter contract: skill_id, source_kind (custom|external), name, description, install_command, install_source, trust_tier, curated_status, target_agents, provenance_status, source_path, risk_notes, promotion_policy, provenance_evidence, selector_mode, notes).
- Define `config/schemas/skills-catalog-index.schema.json` (version, generated_at, entries: array of authoring frontmatter + body_path).
- Add minimal schema validation test `tests/test_skills_catalog_schemas.py`.
- Introduce (per plan) `docs/src/authoring/skills/external/` layout (one MDX per external skill with YAML frontmatter + body for prose).
- Update `wagents/external_skills.py` (and catalog_rows, docs/generate, validate, site_model) for dual-read (bundle-first + fallback) during transition.
- Update `wagents/docs/generate.py` (and research) to emit the index bundle from authoring sources + produce catalog MDX.
- Update sync-manifest, docs-artifact-registry, AGENTS.md §2.7 notes, CONTRIBUTING, pre-commit/CI gates for the new authoring path + generate step.
- One-time migration script (or manual seed) from legacy `config/external-skills.md` rows → per-skill authoring MDX (preserving notes/install blocks as body where appropriate).
- W0 scaffolding + schema + OpenSpec; subsequent waves per the parallel DAG plan (migrate, dual-read, generate consumers, policy, tests, CI, archive).

## Out Of Scope

- Big-bang deletion or replacement of `config/external-skills.md` (dual-read window required).
- Moving MCP/hook/harness-surface registries into docs authoring in Phase 1.
- Treating generated catalog MDX pages themselves as the SSOT (they remain generated; authoring MDX + emitted index are the new source).
- Full rewrite of all ~100+ curated rows in W0 (wave-based parallel authoring migration in later waves).
- Changes to runtime `skills/` custom skill authoring (SKILL.md frontmatter stays).

## Affected Users And Tools

- Maintainers curating external skills (new workflow: edit per-skill MDX frontmatter/body under authoring/ instead of appending blocks to flat external-skills.md).
- `wagents skills sync`, `docs generate`, `validate`, discover inventory, site build.
- Consumers of catalog rows / public indexes (docs site, harness parity, research emitters).

## Generated Surfaces To Refresh

- `config/docs-artifact-registry.json` (new authoring source + generated-registries.json).
- `docs/src/content/docs/skills/catalog/external/*.mdx` (still generated).
- `README.md` (via wagents readme), any install hubs.
- `generated-registries.json` (new committed bundle).

## Risks

- Pre-commit / CI breakage on stale generated artifacts if authoring changes without `docs generate`.
- Parser drift during dual-read window (mitigate with parity tests + schema).
- Body content migration from prose notes in external-skills.md (preserve intent; use research artifacts for enrichment).
- Scope creep into Bucket B (explicitly rejected).
