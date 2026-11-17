# Summary

Enforce unique prompt text inside canonical skill eval manifests so coverage
counts represent distinct behavioral scenarios rather than repeated dispatch
strings.

# Problem

`wagents eval coverage` counts every case in `evals/evals.json`, while
`wagents eval validate` currently checks that prompts exist but not that they are
distinct. Duplicate prompts can inflate coverage counts and weaken release
evidence.

# Proposed Change

- Reject duplicate stripped `prompt` values within each canonical
  `skills/<name>/evals/evals.json` manifest.
- Keep legacy single-scenario eval JSON files unchanged.
- Update skill-creator audit feedback to flag duplicate prompts as eval quality
  debt.
- Update docs and release evidence after the validator and existing manifests
  are clean.

# Non-Goals

- Do not add fuzzy, semantic, or cross-skill prompt deduplication.
- Do not delete eval cases just because their prompts were duplicates.
- Do not change live eval execution behavior.
