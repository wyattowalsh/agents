# Validation Matrix

| Surface | Command | Expected Result | Notes |
|---------|---------|-----------------|-------|
| OpenSpec | `uv run wagents openspec validate` | Pass | Validates this change and any spec deltas. |
| Python lint | `uv run ruff check skills/nerdbot tests/` | Pass | Covers package, scripts, and tests. |
| Python format | `uv run ruff format --check skills/nerdbot tests/` | Pass | Formatting check only unless explicitly applying format. |
| Type checking | `uv run ty check` | Pass | Repository type check. |
| Nerdbot tests | `uv run pytest tests/test_nerdbot*.py tests/test_package.py tests/test_skill_creator_audit.py -q` | Pass | Includes package and audit regression coverage. |
| Asset validation | `uv run wagents validate` | Pass | Skill and agent metadata remain valid. |
| Eval validation | `uv run wagents eval validate` | Pass | Nerdbot evals remain parseable and non-duplicative. |
| Skill audit | `uv run python skills/skill-creator/scripts/audit.py skills/nerdbot/ --format json` | Pass with acceptable score | Confirms skill quality gates. |
| Packaging | `uv run wagents package nerdbot --dry-run` | Pass | Confirms package portability without writing release ZIPs. |
| Whitespace | `git diff --check` | Pass | Catches trailing whitespace and patch issues. |

## Blockers

- None known after execution mode was enabled.

## Deferred Checks

- Full optional adapter smoke tests may require extras and fixtures; base behavior must still pass without extras.
- Generated docs refresh should happen after public behavior and references stabilize.
