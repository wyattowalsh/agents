# Design

## Approach

Extend the existing research + docs pipeline (post-unify) to treat curated-external symmetrically for enrichment:

- Research artifacts now supported for curated-external (30-day stale, separate from custom 90-day).
- `seed_phase_a_research` generalized or new `seed_curated_phase_a` / lazy mode using SKILL.md preview on-demand (no vendoring).
- Batch partitioning and `build_batch_prompt` already route curated; add "emit-waves" output mode that emits structured wave prompts (for orchestrator) instead of (or in addition to) console batches.
- Catalog page generation + rendering: when research artifact exists for curated node, embed under evidence disclaimer (same as custom).
- Site model exposes harness rows, trust tiers, install commands, provenance for curated rows (already partially present; ensure parity in generated catalog).
- Docs instructions spec updated with delta for curated research + enriched pages + emit-waves.

Parity invariant: every Install Now curated ID in `external-skills.md` appears as a skill node (with stub or enriched page) under `/skills/catalog/`.

Lazy upstream: research for curated uses public metadata + optional on-demand fetch (gated); generated build default remains `--no-installed` + no network.

## Data And Control Flow

1. `collect_skill_doc_nodes(include_curated=True)` produces curated-external nodes from config.
2. `wagents docs research --source-type curated-external` (or all) → partitions → builds prompts (or emits waves).
3. Agent writes `docs/src/skill-research/<id>.md` with frontmatter + brief.
4. `update_research_manifest()`.
5. `wagents docs generate` (curated included by default) renders catalog MDX embedding research if present + full metadata row.
6. Sync desired set already includes Install Now curated; catalog must match IDs.

## Integration Points

- `docs research` gains `--emit-waves` flag (or subcommand behavior) producing wave-compatible output.
- Rendering embeds research for source_type in {"custom", "curated-external"}.
- Queries yaml has curated-external entry.
- OpenSpec docs-instructions updated for new scenarios (curated research embedding, emit-waves, catalog parity).
- Tests cover coverage for curated, parity matrix, wave emission.

## Alternatives Rejected

- Full auto-research + commit of curated artifacts in CI: rejected (network, volume, CI-safety; keep optional + lazy).
- Separate catalog surface for curated: rejected (unify goal; enrich in place with source labels).
- Vendoring upstream SKILL.md for curated: rejected (explicit lazy requirement).

## Migration Or Compatibility Notes

- Existing research artifacts (custom) unchanged.
- Curated pages that had no research continue as enriched stubs (with harness metadata); enrichment is additive/opt-in via research artifacts.
- `--no-installed` generate continues to produce curated stubs/pages (now capable of research).
- Manifest and coverage reports now include curated-external.