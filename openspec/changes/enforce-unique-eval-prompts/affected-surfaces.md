# Affected Surfaces

## Source Of Truth

- `skills/*/evals/evals.json` canonical eval manifests: duplicate stripped prompts were rewritten where needed while preserving case IDs and intent.
- `skills/skill-creator/scripts/asset_toolkit/validate_evals.py`: canonical bundled validator now rejects duplicate stripped prompt text within a manifest.
- `skills/skill-creator/scripts/audit.py`: skill audit feedback now reports duplicate eval prompts as coverage quality debt.
- `wagents/docs.py`: generated CLI documentation describes the uniqueness rule.
- `openspec/changes/enforce-unique-eval-prompts/`: change proposal, affected surfaces, design, validation matrix, tasks, and skills lifecycle delta.

## Generated Outputs

- Existing bundled `skills/*/scripts/asset_toolkit/validate_evals.py` copies were synchronized with the canonical validator.
- `README.md` and generated docs artifacts were refreshed through `uv run wagents readme` and `uv run wagents docs generate --no-installed`.
- `planning/manifests/public-release-readiness-evidence.md` records duplicate-prompt-specific validation evidence.

## Downstream Agent Artifacts

- No downstream harness runtime behavior changes.
- No install, sync, or generated OpenSpec tool artifacts are required for this validator-only change.

## Tests

- `tests/test_eval_cli.py` covers duplicate stripped prompt rejection and scans real repo manifests for duplicate stripped prompts.
- `tests/test_skill_creator_audit.py` covers audit feedback for duplicate prompt coverage debt.
- Existing bundled toolkit tests verify asset toolkit copy surfaces remain present.

## Validation Commands

- `uv run wagents eval validate --format json`
- `uv run wagents eval coverage --format json`
- `uv run pytest tests/test_eval_cli.py tests/test_skill_creator_audit.py tests/test_skill_bundled_toolkit.py -q`
- `uv run pytest tests/test_eval_adequacy.py tests/test_eval_cli.py tests/test_eval_ci_flagship.py tests/mcp/test_eval_results.py -q`
- `uv run wagents docs generate --no-installed --check`
- `uv run wagents readme --check`
- `uv run wagents validate --format json`
- `uv run ruff check`
- `uv run ty check`
- `git diff --check`
