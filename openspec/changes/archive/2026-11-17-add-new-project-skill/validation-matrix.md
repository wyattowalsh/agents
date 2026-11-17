## Validation Matrix

| Area                | Command                                                                                 | Required Result                                    |
| ------------------- | --------------------------------------------------------------------------------------- | -------------------------------------------------- |
| OpenSpec            | `uv run wagents openspec validate`                                                      | Passes                                             |
| Skill metadata      | `uv run wagents validate`                                                               | Passes                                             |
| Evals               | `uv run wagents eval validate`                                                          | Passes                                             |
| Catalog schema/data | `uv run python skills/new-project/scripts/validate_catalog.py --format json`            | `ok: true`                                         |
| Preferences CLI     | `uv run python skills/new-project/scripts/preferences.py validate --format json`        | `ok: true`                                         |
| Preflight CLI       | `uv run python skills/new-project/scripts/preflight.py --path . --format json`          | Emits JSON without reading secrets                 |
| Blueprint CLI       | `uv run python skills/new-project/scripts/blueprint.py --help`                          | Exits 0                                            |
| Plan validator CLI  | `uv run python skills/new-project/scripts/validate_plan.py --help`                      | Exits 0                                            |
| Skill audit         | `uv run python skills/skill-creator/scripts/audit.py skills/new-project/ --format json` | Scores A / 90+ or reports fixable gaps             |
| Package portability | `uv run wagents package new-project --dry-run`                                          | Passes                                             |
| README freshness    | `uv run wagents readme --check`                                                         | Passes, or README regenerated after implementation |

## Additional Checks If Tests Are Added

| Area         | Command                                           |
| ------------ | ------------------------------------------------- |
| Script tests | `uv run pytest tests/test_new_project_scripts.py` |

## Completion Criteria

- The new skill has a dispatch table with an empty-args handler.
- Every reference in `SKILL.md` exists on disk.
- Catalog data validates and has no unresolved capability dependencies.
- Evals cover explicit dispatch, implicit triggers, negative controls, preferences, existing repo repair, docs profiles, cloud opt-in, and safety gates.
- No real secret values or destructive command defaults are present.
