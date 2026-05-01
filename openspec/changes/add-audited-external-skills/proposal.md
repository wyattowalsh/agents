# Proposal

## Problem

The repo has an approved curated external skill install set, but the requested `ljagiello/ctf-skills`, `nextlevelbuilder/ui-ux-pro-max-skill`, and researched `Leonxlnx/taste-skill` sources are not represented in that source of truth or generated docs. The requested install coverage also extends beyond the current default target suffix, so applying the change directly would risk undocumented harness gaps, accidental installation of overlapping bundled skills, or live installs that are not traceable to the external-skill audit findings.

## Intent

Add the audited external skill sources to the curated external skill workflow, install only the approved skills across every supported requested harness, document unsupported harness evidence, and regenerate/validate the public docs surfaces that expose external skills and install coverage.

## Scope

- Add `ljagiello/ctf-skills` to the curated external install source after audit, selecting all 11 CTF skills.
- Add `nextlevelbuilder/ui-ux-pro-max-skill` to the curated external install source after audit, selecting only `ui-ux-pro-max`.
- Add `Leonxlnx/taste-skill` to the curated external install source after audit, selecting only `design-taste-frontend`.
- Expand or supplement target-harness documentation based on actual Skills CLI and harness support discovered on this machine.
- Preserve an explicit avoid note for bundled `ckm:*` skills from `nextlevelbuilder/ui-ux-pro-max-skill` unless the user later requests them.
- Preserve an explicit keep-global-only note for unselected `Leonxlnx/taste-skill` bundle variants unless the user later requests them.
- Attempt live installs for all requested harnesses that have a supported Skills CLI adapter or observable harness-specific skill surface.
- Run the audited CTF tooling installer after dry-run/verification because full setup was requested.
- Regenerate generated docs/site data and README surfaces that reflect curated external skills.
- Run docs-steward review after generation/build to catch documentation drift.

## Out Of Scope

- Promoting external skill contents into repo-owned `skills/` directories.
- Installing bundled `ckm:*` skills from `nextlevelbuilder/ui-ux-pro-max-skill`.
- Installing external repositories that were not part of this approved request or the follow-up `taste-skill` research request.
- Reverting or modifying unrelated dirty worktree changes.
- Guessing unsupported harness behavior without command output or inspected config evidence.

## Affected Users And Tools

- Users relying on `instructions/external-skills.md` for curated third-party skill sync.
- Users reading generated README/docs external skill listings.
- Harness installs for `claude-desktop`, `claude-code`, `chatgpt`, `codex`, `github-copilot-web`, `github-copilot-cli`, `opencode`, `gemini-cli`, `antigravity`, `perplexity-desktop`, `cherry-studio`, and `cursor` variants where supported.
- Future maintainers using `wagents skills sync` to reconcile curated external skills.

## Generated Surfaces To Refresh

- `README.md` from `uv run wagents readme`.
- Docs catalog/site data from `uv run wagents docs generate`.
- Any generated external skill or installed-inventory docs that depend on `instructions/external-skills.md` and the normalized harness inventory.

## Risks

- `ctf-skills` contains offensive-security workflows and write-capable tool permissions; docs and reports must limit usage to authorized CTF/security research.
- The CTF installer can invoke `pip`, `apt`, `brew`, `gem`, `go`, and `sudo`, and writes to `~/.ctf-tools`; run dry-run/verification first and report the exact result.
- Requested harness names may not all map to Skills CLI adapters; unsupported targets must be reported with evidence instead of silently skipped.
- `ui-ux-pro-max-skill` bundles extra `ckm:*` skills with broader API/script surfaces and overlap with existing design workflows; install only `ui-ux-pro-max`.
- `taste-skill` bundles many overlapping style, image-generation, Google Stitch, and output-behavior skills; install only `design-taste-frontend` unless explicitly requested.
- Generated docs/README may also include pre-existing unrelated dirty content; do not claim unrelated changes as part of this work.
