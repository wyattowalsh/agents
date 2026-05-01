# Tasks

## OpenSpec

- [x] Add OpenSpec artifacts for this change.

## Discovery

- [x] [P] Discover exact Skills CLI target adapter IDs for the requested harness set.
- [x] [P] Run harness-master discovery for requested harness install/config surfaces.
- [x] Reconcile requested harness names with discovered adapter names and unsupported evidence.

## Curated External Skills

- [x] Update `instructions/external-skills.md` with the audited `ctf-skills` command and responsible-use notes.
- [x] Update `instructions/external-skills.md` with the audited `ui-ux-pro-max` command and `ckm:*` avoid note.
- [x] Update `instructions/external-skills.md` with the audited `taste-skill` main-skill command and bundle avoid note.
- [x] Update docs/source wording for expanded target coverage where supported.

## Installation

- [x] Install selected external skills across every supported requested harness.
- [x] Run `ctf-skills` installer dry-run from the audited source.
- [x] Run `ctf-skills` installer if dry-run does not reveal a blocker.
- [x] Reconcile supported harness installs with `uv run wagents skills sync --dry-run` and `--apply` when scoped to approved missing curated skills.

## Generated Docs

- [x] Regenerate docs with `uv run wagents docs generate`.
- [x] Regenerate README with `uv run wagents readme`.
- [x] Ensure generated external skill lists visibly include both approved sources or explain target-specific exclusions.

## Verification And Review

- [x] Run `uv run wagents validate`.
- [x] Run `uv run wagents openspec validate`.
- [x] Build docs with `cd docs && pnpm build`.
- [x] Run docs-steward subagent review for docs drift, generated output consistency, external skill visibility, and harness coverage wording.
- [x] Address blocking docs-steward findings and rerun relevant validation.
- [x] Report installed-by-harness results, unsupported harness blockers, CTF installer results, docs changes, and validation evidence.

Docs-steward health note: `scripts/health-check.py --all` reported 8 stale hand-maintained pages outside this change's external-skill generated surfaces. No blocking finding was found for the approved external skill visibility or harness coverage docs, so the stale hand-maintained pages are tracked as out-of-scope maintenance debt.
