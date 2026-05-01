# Release Checklist

## Scope

This checklist gates release readiness for the agents platform overhaul planning/control-plane work. It is not a deployment script.

## Pre-Release

- [ ] Confirm branch is `main` and no branch switch is required.
- [ ] Confirm unrelated dirty files are not staged.
- [ ] Confirm all child OpenSpec changes are complete.
- [ ] Confirm parent `agents-platform-overhaul` is complete or has only explicitly deferred tasks.
- [ ] Confirm forbidden surfaces are excluded unless explicitly approved.
- [ ] Confirm no secrets, credentials, or live user config values appear in diffs or reports.

## Validation

- [ ] Run `uv run wagents openspec validate`.
- [ ] Run targeted `git diff --check` for release-owned paths.
- [ ] Review child status JSON for all release lanes.
- [ ] Run a lane-scoped code/doc review and address blockers.
- [ ] Record skipped checks and why they are safe to defer.

## Documentation

- [ ] Decide whether generated docs are regenerated now or deferred.
- [ ] If regenerated, review generated docs separately from planning changes.
- [ ] Ensure `planning/95-migration/50-release-notes.md` lists child lanes, commits, validation commands, exclusions, and known risks.

## Release Candidate

- [ ] Stage with exact pathspecs.
- [ ] Commit one logical release unit with a conventional commit message.
- [ ] Confirm `git status --short --branch` shows only intended staged/committed changes affected by the release.
- [ ] If creating a PR, include rollback and archive readiness sections.

## Post-Merge

- [ ] Re-run `uv run wagents openspec validate` from merged `main`.
- [ ] Confirm generated docs/instruction mirrors are either synchronized or explicitly deferred.
- [ ] Confirm archive checklist is ready before moving OpenSpec changes.

Deferred parent tasks may allow a release candidate when they are explicitly recorded and out of scope, but they block OpenSpec archive unless resolved or re-scoped in the archive evidence.
