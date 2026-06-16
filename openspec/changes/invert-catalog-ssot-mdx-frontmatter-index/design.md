# Design

## Architecture (Brief)

**Human SSOT layer (Phase 1, external only):**
- `docs/src/authoring/skills/external/<skill-id>.mdx` — YAML frontmatter (per `skills-catalog-authoring.schema.json`) + markdown body (prose, notes, provenance evidence snippets, optional research links).
- Frontmatter carries the structured fields previously derived/scraped from `config/external-skills.md` (skill_id, source_kind="external", install_*, trust_tier, curated_status, target_agents, provenance_*, risk_notes, promotion_policy, selector_mode, notes, ...).
- `source_kind` supports "custom" for future unification but Phase 1 authoring focuses on external.

**Generated machine bundle (committed, consumed by code):**
- `wagents docs generate` (and supporting catalog/index writers) emits `docs/src/generated/generated-registries.json` (or top-level equivalent; indexed by `config/docs-artifact-registry.json`).
- Index shape: `{ "version": 1, "generated_at": "...", "entries": [ { ...authoring frontmatter..., "body_path": "docs/src/authoring/skills/external/<id>.mdx" }, ... ] }` validated by `skills-catalog-index.schema.json`.
- Catalog MDX pages, site model, and public rows continue to be derived from the index + research artifacts (no change to output shape for consumers).

**Dual-read transition (consumers):**
- `wagents/external_skills.py`: prefer bundle/index when present (and fresh), fall back to legacy `config/external-skills.md` parse + curated_entry_by_name etc. Emit deprecation notes in logs when falling back.
- `wagents/catalog_rows.py`, `site_model.py`, `docs/generate.py`, `validate.py` (quarantine), discover config_inventory: retargeted to read the new index first.
- `config/external-skills.md` remains editable in the short term (or becomes output of a reverse emit for rollback) but is no longer the parse source after cutover.

**Schemas + validation:**
- New schemas under `config/schemas/` (matching style of `skill-registry-policy.schema.json`, `harness-surface-registry.schema.json` etc.).
- `tests/test_skills_catalog_schemas.py`: jsonschema validate (when available) + structural asserts for minimal samples.

**W0 deliverable (this change):**
- Scaffolding only: the change dir + 5 artifacts, the two schemas, the schema test. No consumer rewrites yet (those land in later waves per DAG).

**Later waves (per plan):**
- W1: authoring dir seed + migration helper + frontmatter examples from legacy rows.
- Dual-read implementation + parity guards.
- Generate emission of index + update of docs artifact registry.
- Consumer retarget + test lock-in.
- Policy / AGENTS.md / CONTRIBUTING / pre-commit updates.
- CI + full W7 validation matrix.
- Archive of this change after sign-off.

## Data Flow (High Level)

Authoring MDX (edit) → docs generate → committed index.json (SSOT for machines) + regenerated catalog MDX (reference) → wagents external_skills / catalog_rows / validate / discover (bundle-first) + site build.

Legacy path temporarily preserved for safety.

## Alternatives Rejected (Summary)

- Generated MDX as SSOT: violates "human authoring" requirement and Diátaxis layering.
- Stuffing all catalog rows into AGENTS.md: rejected (policy bank, not data store).
- Full Bucket A (incl. MCP/hooks) in same change: deferred to keep scope bounded.
- Immediate delete of config/external-skills.md: would break headless CI and require perfect migration first.

## References

- Memory/panel: Option B phased invert, external slice only, confidence ~0.78.
- Anchor prior: openspec/changes/add-docs-authoring-ssot/ (scaffolded in planning).
- Related: catalog_rows.py, external_skills.py, docs-artifact-registry, AGENTS.md §2.7.
