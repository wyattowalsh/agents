<!--
Skill change PR template. Delete sections that do not apply, but keep the
checklist — reviewers use it to confirm eval, docs, and packaging coverage.
-->

## Summary

<!-- What skill(s) changed and why, in 1-3 sentences. -->

## Type of change

- [ ] New skill
- [ ] Existing skill: behavior/body change
- [ ] Existing skill: frontmatter/metadata only
- [ ] Curated external skill catalog entry (see `AGENTS.md` §2.7)

## Eval coverage

- [ ] `skills/<name>/evals/evals.json` exists and covers the changed behavior
- [ ] `uv run wagents eval validate --format json` passes
- [ ] `uv run wagents eval adequacy --skill <name>` reviewed (R3/R4 skills need E4 signals)
- [ ] N/A — change does not affect skill behavior (docs/typo only)

## Validation run locally

- [ ] `uv run wagents validate`
- [ ] `uv run wagents docs generate --no-installed` (if the skill has a docs page)
- [ ] `uv run wagents skills sync --dry-run` (if install/discovery behavior changed)
- [ ] `uv run pytest` (relevant subset)

## Docs & packaging

- [ ] Docs page regenerated (`wagents docs generate`) if this skill affects public catalog content
- [ ] `wagents readme` regenerated if this skill affects the README skill table
- [ ] Packaging unaffected, or `uv run wagents package <name> --dry-run` passes

## Security / trust notes

<!-- Any new network egress, shell execution, credential handling, or third-party source? -->
