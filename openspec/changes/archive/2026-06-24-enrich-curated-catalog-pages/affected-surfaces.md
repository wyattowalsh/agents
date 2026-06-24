# Affected Surfaces

## Source Of Truth

- `config/external-skills.md` — curated external source (Install Now entries for parity).
- `wagents/skill_docs.py` — `collect_skill_doc_nodes`, curated stub handling, source_type.
- `wagents/skill_research.py` — research artifacts, `seed_phase_a_research`, `partition_skills_for_research`, `build_batch_prompt`, coverage, manifest, stale windows for curated-external.
- `wagents/docs.py` — `docs research` (source-type, include, seed, emit-waves), `docs generate`, research embedding.
- `wagents/site_model.py`, `wagents/rendering.py` — skill node metadata (trust tiers, harness rows, install commands), catalog page rendering for research.
- `wagents/external_skills.py`, `wagents/installed_inventory.py` — provenance, trust, target agents for curated rows.
- `docs/src/content/docs/skills/catalog/*.mdx` (generated), hand-maintained overlays under catalog/.
- `docs/src/components/SkillCatalog.astro` / related UI for enriched curated filters/rows.
- `openspec/specs/docs-instructions/spec.md` — canonical spec to receive delta.
- `tests/test_skill_research.py`, `tests/test_docs.py`, `tests/test_site_model.py`, sync tests.
- `wagents/data/skill-research-queries.yaml` — curated-external templates.

## Generated Outputs

- `docs/src/content/docs/skills/catalog/<curated-id>.mdx` (enriched with research when present).
- `docs/src/content/docs/skills/all.mdx`, `skills/index.mdx`, `skills/install.mdx`, `external-skills.mdx`.
- `docs/src/skill-research/<curated-id>.md` artifacts.
- `docs/src/generated-skill-research-index.mjs`.
- Generated site data / skill indexes containing curated metadata.
- `README.md` (if research or catalog stats surface there).

## Downstream Agent Artifacts

- Orchestrator / subagent wave prompts from research batches (emit-waves).
- Harness sync desired rows matching catalog curated IDs.

## Tests

- Research coverage, artifact write, batch prompt, manifest, stale checks for curated-external.
- Docs generate with/without curated research; embedding in catalog pages.
- Parity assertions: curated skill IDs present in both catalog and external-skills/sync.
- No local-path leaks in enriched curated pages.

## Validation Commands

- `uv run wagents openspec validate`
- `uv run pytest tests/test_skill_research.py tests/test_docs.py tests/test_site_model.py`
- `uv run wagents docs research --dry-run --source-type curated-external --no-installed`
- `uv run wagents docs research --seed-from-repo --source-type custom` (parity)
- `uv run wagents docs generate --no-installed`
- `uv run wagents docs generate --include-installed` (local)
- `uv run wagents skills sync --dry-run`
- `uv run wagents validate`
- `cd docs && pnpm build`
- `rg -n 'research' docs/src/content/docs/skills/catalog/ --include '*.mdx' | head -5` (spot check embedding)