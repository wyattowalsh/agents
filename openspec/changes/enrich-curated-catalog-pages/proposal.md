# Proposal

## Problem

Curated external skill stubs (from `config/external-skills.md`) produce minimal catalog pages lacking the enriched research briefs, harness rows, trust tiers, install commands, and lazy upstream SKILL.md previews available to repo-owned skills. Catalog ↔ harness parity is incomplete (skill IDs on `/skills/catalog/` vs `external-skills.md`/sync), and research emission lacks wave-orchestrator support ("emit-waves") for batch enrichment of curated pages.

## Intent

Enrich curated catalog pages and research artifacts so curated-external entries support the same enrichment surfaces as custom skills (research briefs, parity, tiers, commands, lazy previews). Add emit-waves mode for research batching. Update docs-instructions spec. Preserve lazy (on-demand, CI-safe) semantics; no full upstream vendoring.

## Scope

- Extend `wagents/skill_research.py`, `seed_phase_a_research`, coverage, manifest, and batch prompts to curated-external (and installed where appropriate).
- Support research artifacts under `docs/src/skill-research/` for curated stubs.
- Update `wagents/docs.py` (research, generate) and rendering/site_model to embed research + harness metadata for curated catalog pages.
- Add `--emit-waves` / wave emission support (batch prompts consumable by orchestrator subagent waves).
- Ensure catalog/harness parity: same skill IDs appear for Install Now curated in generated catalog and sync desired set.
- Delta to `openspec/specs/docs-instructions/spec.md`.
- Update catalog UI/components if needed for enriched curated rows.

## Out Of Scope

- Vendoring full upstream SKILL.md bodies into repo for curated (lazy only).
- Mandatory network research in CI for curated pages.
- Auto-editing `config/external-skills.md`.
- Promoting stubs to repo-owned skills.
- Full research for all 300+ curated in this change (focus on pipeline + samples).

## Affected Users And Tools

- Docs readers on `/skills/catalog/` and `/external-skills/` seeing enriched curated entries.
- Maintainers running `wagents docs research` and `docs generate` for catalog parity.
- Agents using orchestrator waves for research emission.
- `wagents skills sync` users expecting matching curated rows.

## Generated Surfaces To Refresh

- Generated catalog MDX pages and hubs via `uv run wagents docs generate`.
- `docs/src/skill-research/*.md` (curated entries).
- `docs/src/generated-skill-research-index.mjs`.
- Possibly `docs/src/generated-site-data.mjs` and skill indexes.

## Risks

- Curated research must stay evidence-only with disclaimers (no authority).
- Lazy upstream must not break CI (no network in default `--no-installed` generate).
- Parity must not regress existing custom-only or sync behaviors.
- Batch size and wave prompts must keep research artifacts concise.