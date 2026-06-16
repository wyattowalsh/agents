# Tasks

## OpenSpec / W0 Scaffolding (T-001..T-008) — this change

- [ ] T-001: Create `openspec/changes/invert-catalog-ssot-mdx-frontmatter-index/` directory and 5 artifacts (proposal, design, affected, validation-matrix, tasks).
- [ ] T-002: Write `proposal.md` (dual-SSOT problem statement; per-skill MDX + frontmatter index intent; Phase 1 external-only scope).
- [ ] T-003: Write `design.md` (brief architecture: authoring MDX frontmatter → docs generate → committed index bundle; dual-read consumers; schemas).
- [ ] T-004: Write `affected-surfaces.md` (list all readers/writers: external_skills, catalog_rows, docs/generate, docs-artifact-registry, AGENTS.md, tests, etc.).
- [ ] T-005: Write `validation-matrix.md` (W0 commands + full W7 matrix commands extracted/copied from plan DAG).
- [ ] T-006: Write this `tasks.md`; map OpenSpec items + reference full wave DAG (W0–W5, M1–M5, T-00x).
- [ ] T-007: Create `config/schemas/skills-catalog-authoring.schema.json` (frontmatter fields exactly as specified: skill_id, source_kind (custom|external), name, description, install_command, install_source, trust_tier, curated_status, target_agents, provenance_status, source_path, risk_notes, promotion_policy, provenance_evidence, selector_mode, notes; match style of skill-registry-policy.schema.json).
- [ ] T-008: Create `config/schemas/skills-catalog-index.schema.json` (version const 1, generated_at, entries array of authoring frontmatter + body_path).
- [ ] T-009: Create `tests/test_skills_catalog_schemas.py` (minimal tests: file load, structural + jsonschema validation if available; sample external + index payloads).
- [ ] T-010: `uv run pytest tests/test_skills_catalog_schemas.py -q` + `uv run wagents openspec validate` green for scaffolding.

## W0 Foundation (per plan; serial baseline before parallel)

- [ ] T-011 (W0): Grep gate + baseline (pytest slice, wagents validate, docs counts snapshot).
- [ ] T-012 (W0): Schema stage complete (authoring + index landed + test).
- [ ] T-013 (W0): OpenSpec change committed as anchor.
- [ ] T-014 (W0): Update docs-artifact-registry.json + sync-manifest.json with authoring path + generated index declaration (or stub).

## W1 Parallel (migrate + seed authoring)

- [ ] T-015..T-0xx: Per-plan wave tasks for one-time migration script (config/external-skills.md → authoring MDX per-skill with frontmatter + body notes).
- [ ] Seed initial external examples under `docs/src/authoring/skills/external/` (frontmatter complete, body populated from legacy prose).
- [ ] Update `wagents/external_skills.py` skeleton for bundle detection (no full dual yet).
- [ ] Frontmatter examples validated against authoring schema.
- [ ] Parallel fan-out per curated row groups (as sized in plan DAG).

## W2 Dual-Read + Consumers (parallel lanes)

- [ ] Retarget `read_external_skill_entries` + `curated_entry_by_name` / `entry_to_public_row` to prefer generated index.
- [ ] Implement fallback to legacy parser when index absent (with log note).
- [ ] Update catalog_rows, site_model, docs/generate, validate quarantine, discover inventory to dual-read path.
- [ ] Add parity tests: legacy parse output == index-derived rows (for seed set).
- [ ] Schema-enforced load of index in generate path.

## W3 Generate + Emission

- [ ] Implement `wagents/docs/generate.py` (or dedicated catalog index writer) emission of `generated-registries.json` (or path per artifact registry) from authoring MDX frontmatter + body_path.
- [ ] Regenerate catalog MDX pages from the new index + research (no behavior change for public output).
- [ ] Update docs build / site model consumption of the bundle.
- [ ] Ensure `docs generate --no-installed` (CI default) emits fresh index.
- [ ] Add generated index to git (committed machine bundle, not browsable MDX).

## W4 Policy + Docs + AGENTS

- [ ] Update AGENTS.md §2.7, instructions/*, CONTRIBUTING.md, .github/*-instructions.md to document new authoring workflow ("edit per-skill MDX under docs/src/authoring/skills/external/").
- [ ] Add "GENERATED FROM authoring MDX + index" markers on derived surfaces.
- [ ] Update pre-commit hooks / CI scripts that lint external-skills.md or require manual sync.
- [ ] Policy notes for dual-read window and cutover criteria.

## W5 Tests + CI + Gates

- [ ] Lock-in: update/extend `test_external_skills.py`, `test_docs.py`, `test_site_model.py`, `test_validate.py`, catalog parity tests for index path.
- [ ] Add pre-commit gate that fails on authoring change without matching `docs generate` index.
- [ ] CI matrix includes: docs generate, skills sync --dry-run, schema tests, wagents validate, openspec validate, docs build.
- [ ] Research emission / wave support parity for authoring sources (if emit-waves touches catalog).

## Merge Gates M1–M5 (plan)

- M1: W0 complete + baseline green (schemas + OpenSpec + test).
- M2: Migration seeds + dual-read skeleton land; parity on seed set.
- M3: Generate emission + index committed + catalog regen green.
- M4: All consumers retargeted; policy/docs updated; no regression on --no-installed outputs.
- M5 (W7): Full validation matrix (see validation-matrix.md) + user sign-off; prepare archive.

## Documentation

- [ ] Refresh AGENTS.md, CONTRIBUTING, docs instructions, kb notes only via the approved workflow.
- [ ] Do not hand-edit generated catalog MDX or the emitted index.
- [ ] Invoke docs-steward after generate steps in later waves.

## Verification

- [ ] All T-00x executed or explicitly noted.
- [ ] `uv run pytest tests/test_skills_catalog_schemas.py`
- [ ] `uv run wagents openspec validate`
- [ ] W7 matrix commands (full generate + sync --dry-run + build + tests + validate) as listed in validation-matrix.md.
- [ ] Catalog parity (curated IDs in index match legacy + catalog pages).
- [ ] Dual-read fallback exercised in tests (index-absent mode).
- [ ] Update this tasks.md to [x] on completion of each item; do not auto-archive.

## Wave / Task Count Reference (from plan)

W0–W5 with ~40+ hyperfine atomic tasks (T-001…); explicit depends_on + parallel_group lanes (schema, migrate, dual-read, generate, consumers, policy, CI, archive). External-skills authoring only for Phase 1.
