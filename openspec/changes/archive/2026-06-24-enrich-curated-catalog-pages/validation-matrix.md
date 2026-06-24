# Validation Matrix

| Surface | Command | Expected Result | Notes |
|---------|---------|-----------------|-------|
| OpenSpec | `uv run wagents openspec validate` | Pass |  |
| Asset + skill validation | `uv run wagents validate` | Pass |  |
| Research unit tests (curated support) | `uv run pytest tests/test_skill_research.py -k "curated or research or coverage or wave or emit"` | Pass | Extend tests for curated-external. |
| Docs + site model tests | `uv run pytest tests/test_docs.py tests/test_site_model.py` | Pass | Include curated research embedding + parity. |
| Sync parity | `uv run wagents skills sync --dry-run` | Curated Install Now IDs appear in missing/present as expected; no ID drift vs catalog |  |
| Curated research planner | `uv run wagents docs research --dry-run --source-type curated-external --no-installed --batch-size 5` | Lists batches; prompts contain curated templates |  |
| Emit-waves (new) | `uv run wagents docs research --emit-waves --source-type curated-external --dry-run` | Structured wave prompt(s) emitted (no auto-write) |  |
| Seed custom (baseline) | `uv run wagents docs research --seed-from-repo --source-type custom --no-installed` | Custom artifacts present; coverage reported |  |
| Curated research coverage check | `uv run wagents docs research --check-research --source-type curated-external --no-installed` | Passes when 100% or documents gap | Optional gate. |
| CI-parity docs generate | `uv run wagents docs generate --no-installed` | Succeeds; curated pages generated (enriched where artifacts exist) |  |
| Research embedding spot-check | `uv run wagents docs generate --no-installed && rg -l 'research' docs/src/content/docs/skills/catalog/ --include '*.mdx' \| head -3` | Shows enriched curated pages if artifacts seeded |  |
| Docs production build | `cd docs && pnpm build` | Pass |  |
| Local parity + installed | `uv run wagents docs generate --include-installed` | Pass locally |  |
| Patch hygiene | `git diff --check` | Pass |  |

## Blockers

- Research artifacts for curated must include explicit "evidence, not authority" disclaimer.

## Deferred Checks

- Do not run live network research without dry-run or explicit approval for sampled curated entries.
- Do not commit 100s of curated research artifacts in initial change (focus pipeline + validation + a few samples if needed).
- `--emit-waves` output is for agent consumption; do not assert exact prompt text beyond structure in first pass.