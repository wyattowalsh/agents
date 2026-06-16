# Tasks

## Implementation

- [ ] Extend research artifact support, stale logic, coverage, manifest, and `seed_phase_a_research` (or new lazy seed) to curated-external source type in `wagents/skill_research.py`.
- [ ] Update batch partitioner + `build_batch_prompt` to handle curated (already routes via queries); add curated-external template in `wagents/data/skill-research-queries.yaml` if missing.
- [ ] Add `--emit-waves` (or equivalent) to `docs research` in `wagents/docs.py` that emits orchestrator-consumable wave prompt(s) for the selected batches/source (dry-run friendly).
- [ ] Update `wagents/docs.py` generate + `wagents/rendering.py` / site model to embed research artifacts (with disclaimer) for curated-external nodes when artifact present (symmetric to custom).
- [ ] Ensure generated catalog pages + `external-skills.mdx` / hubs expose harness rows, trust tiers, install commands, provenance for curated (parity).
- [ ] Add or update catalog component/UI bits if new filters/metadata for enriched curated rows required.
- [ ] Implement catalog ↔ harness parity check helper (IDs match for Install Now curated).

## Documentation

- [ ] Create this OpenSpec change (proposal, affected-surfaces, design, validation-matrix, tasks, specs delta).
- [ ] Update `openspec/specs/docs-instructions/spec.md` with delta (new scenarios for curated research embedding, enriched catalog pages, emit-waves, parity).
- [ ] Refresh any hand-maintained references (CONTRIBUTING, AGENTS.md, wiki) only if source-of-truth guidance changes.
- [ ] Do not hand-edit generated catalog pages.

## Verification

- [ ] Run the validation matrix commands (research tests, docs generate, sync dry-run, build, coverage checks, emit-waves dry-run).
- [ ] Confirm parity: sample curated ID appears in `external-skills.md`, in sync --dry-run desired, and has (stub or enriched) `/skills/catalog/<id>/` page.
- [ ] `uv run wagents openspec validate`.
- [ ] Seed a few curated research samples (optional, via manual or wave) and verify embedding + no regression on custom.
- [ ] Run full test suite slice and docs build.