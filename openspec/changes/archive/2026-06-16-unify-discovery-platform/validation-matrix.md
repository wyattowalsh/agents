# Validation Matrix

| Surface | Command | Expected Result | Notes |
|---------|---------|-----------------|-------|
| Skill portable check | `uv run python skills/discover-skills/scripts/check.py` | Exit 0 | Includes validate, evals, package dry-run, audit >= 80. |
| Discovery unit tests | `uv run pytest tests/test_discovery_coordinator.py tests/test_discovery_schemas.py tests/test_discovery_gap_engine.py tests/test_discover_journal_store.py tests/test_skills_no_wagents.py -q` | All pass | Coordinator cap, schema contracts, journal v2. |
| Parity guard | `uv run python scripts/check_discovery_parity.py` | `ok: true` | Repo skill count matches inventory scan. |
| Asset validation | `uv run wagents validate` | Pass | Skill frontmatter across repo. |
| Manual W0 pipeline | Run coordinator-contract W0 commands | `gap-report.json` + wave-2 manifest with `expected_count <= 24` | Artifacts under `artifacts/<session_id>/`. |
| Coordinator verify | `coordinator.py verify --manifest ... --artifacts ...` | `ok: true` only when all scout artifacts present | Fallback resolves `{task_id}.json` in artifacts dir. |
| OpenSpec | `uv run python skills/openspec-workflow/scripts/openspec_cli.py validate` | Pass | All change artifacts present before archive. |

## Blockers

- None after affected-surfaces and validation-matrix are committed.

## Deferred Checks

- Live `npx skills find` scout dry-run against registry (network-dependent).
- Full W2 scout wave execution with parallel subagents (manual orchestration).