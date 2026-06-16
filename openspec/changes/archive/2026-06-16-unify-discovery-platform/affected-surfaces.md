# Affected Surfaces

## Source Of Truth

- `skills/discover-skills/SKILL.md` — orchestration, dispatch, validation contract, coordinator workflow.
- `skills/discover-skills/data/discovery-taxonomy.json` — domain taxonomy and scout query seeds.
- `skills/discover-skills/data/agent-targets.json` — install command agent allowlist.
- `skills/discover-skills/data/schemas/*.schema.json` — JSON contracts for gap reports, manifests, scout artifacts.
- `skills/discover-skills/scripts/*.py` — gap engine, scans, coordinator, merge, validate, journal store.
- `skills/discover-skills/references/coordinator-contract.md` — W0 commands, verify gate, merge.
- `skills/discover-skills/references/scout-templates.md` — W2 scout spawn prompts (manifest-driven).
- `skills/discover-skills/evals/evals.json` — discovery workflow eval cases.
- `scripts/check_discovery_parity.py` — repo skill count parity guard.
- `openspec/changes/unify-discovery-platform/` — change-control artifacts.

## Delegated Boundaries (subprocess only)

- `skills/skill-router/scripts/skill_index.py` — inventory scan input.
- `skills/harness-master/scripts/discover_surfaces.py` — harness surface scan input.

## Generated Outputs

- `skills/discover-skills/references/gap-analysis.md` via `render_gap_reference.py`.
- `dist/discover-skills-*.skill.zip` via skill packaging dry-run.

## Tests

- `tests/test_discovery_gap_engine.py`
- `tests/test_discovery_coordinator.py`
- `tests/test_discovery_schemas.py`
- `tests/test_discover_journal_store.py`
- `tests/test_skills_no_wagents.py`

## Validation Commands

- `uv run python skills/discover-skills/scripts/check.py`
- `uv run pytest tests/test_discovery_coordinator.py tests/test_discovery_schemas.py tests/test_discovery_gap_engine.py tests/test_discover_journal_store.py tests/test_skills_no_wagents.py -q`
- `uv run python scripts/check_discovery_parity.py`
- `uv run wagents validate`