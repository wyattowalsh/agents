## Summary

Create `review` as the canonical first-party skill for evidence-first code review, scoped/PR/full audits, simplification review, source/provenance review, and specialist review lenses.

## Why OpenSpec

This changes public skill names, skill routing semantics, agent delegation, eval coverage, generated catalog rows, generated docs, README output, and multi-harness sync behavior. It removes existing overlapping first-party public skill entrypoints, so the migration needs a durable change record and validation matrix.

## Problem

The repository currently exposes overlapping first-party review workflows:

- `honest-review` previously owned evidence-first code review and approval-gated fix passes.
- `simplify` previously owned behavior-preserving simplification review and optional narrow edits.
- `external-skill-auditor` previously owned source/provenance review for third-party skills.
- `code-reviewer` and `security-auditor` agents duplicate narrow slices of the same review protocol.

This fragmentation makes review behavior harder to discover, harder to validate across harnesses, and easier to drift between Claude Code, Codex, OpenCode, Grok Build CLI, and generic Skills CLI installs.

## Proposed Change

Add `skills/review/` as the canonical first-party review skill with portable frontmatter and progressive-disclosure references. The skill dispatches by explicit argument, detected diff state, target path, PR/range, source/provenance mode, simplification mode, specialist lens, output format, history/delta/learnings commands, and approval-gated fix requests.

Delete `honest-review`, `simplify`, and `external-skill-auditor` as skills and remove their installable/catalog surfaces. Their behavior is folded into `/review`, `/review simplify`, and `/review source`. Keep read-only agents as agents, but make them delegate their protocol to `/review` with the appropriate lens.

Document external review skill research under `docs/src/skill-research/review.md`. Keep third-party skills as external evidence/catalog rows; do not vendor them into `skills/`.

## Generated Surfaces To Refresh

- `docs/src/authoring/skills/review.mdx` via `uv run wagents catalog sync-authoring`
- `docs/public/generated-registries/skills-catalog-index.json` and generated catalog pages via `uv run wagents docs generate`
- `README.md` via `uv run wagents readme`
- docs static output via `uv run wagents docs build`

## Non-Goals

- Do not preserve legacy skill directories or wrapper aliases; active guidance points to `/review`.
- Do not add a root `model` override or portable skill hooks unless harness validation proves they are cross-target safe.
- Do not run `wagents skills sync --apply`, live `npx skills add`, branch creation, commit, push, stash, or destructive cleanup.
- Do not vendor third-party review skill files into this repository.
