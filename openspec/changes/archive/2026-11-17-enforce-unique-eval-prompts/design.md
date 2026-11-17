# Design

## Approach

Add duplicate detection at the existing canonical eval manifest validation point. The validator already iterates each `evals` array to check required `prompt` and `expected_output` strings, so the smallest correct change is to track stripped prompt text within that same loop and emit an error when a later case repeats an earlier case.

Skill audit feedback uses the same stripped-prompt definition and reports duplicate prompts as evaluation coverage quality debt. Existing manifests are repaired by changing prompt text, not by deleting cases or renaming IDs.

## Data And Control Flow

1. `wagents eval validate` loads each canonical `skills/<name>/evals/evals.json` manifest.
2. For each manifest, validation keeps a per-manifest `seen_prompts` map from stripped prompt text to the first eval index.
3. Non-string or blank prompts continue to use the existing missing-prompt error.
4. Repeated stripped prompt text emits an error that names the later eval and the earlier eval index.
5. Valid unique prompts are stored and validation continues to check the remaining case fields.

## Integration Points

- `skills/skill-creator/scripts/asset_toolkit/validate_evals.py` owns the reusable validation behavior and is synchronized into bundled skill toolkit copies.
- `skills/skill-creator/scripts/audit.py` owns human-facing skill quality feedback for duplicate eval prompts.
- `tests/test_eval_cli.py` covers CLI rejection and real-repo manifest uniqueness.
- `tests/test_skill_creator_audit.py` covers audit feedback.
- `wagents/docs.py` feeds the generated CLI documentation that describes canonical eval manifest requirements.

## Alternatives Rejected

- Cross-skill prompt deduplication: rejected because repeated prompts across different skills can be legitimate and would create noisy coupling.
- Fuzzy or semantic duplicate detection: rejected because it is subjective and would make validation unstable.
- Deleting duplicate cases: rejected because case IDs and expected outputs can carry useful intent; rewriting prompts preserves coverage while making the scenario distinction explicit.

## Migration Or Compatibility Notes

Legacy single-scenario eval JSON files are unchanged. The new rule applies only within one canonical `evals/evals.json` manifest and only compares prompt text after trimming surrounding whitespace.
