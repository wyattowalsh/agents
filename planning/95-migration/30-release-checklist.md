# Release Checklist

## Scope

This checklist records completed release readiness for the agents platform overhaul planning/control-plane work and separates it from the current archive cleanup commit gate. It is not a deployment script.

## Pre-Release

- [x] Confirm branch is `main` and no branch switch is required.
- [x] Confirm unrelated dirty files are not staged.
- [x] Confirm all child OpenSpec changes are complete.
- [x] Confirm parent `agents-platform-overhaul` is complete or has only explicitly deferred tasks.
- [x] Confirm forbidden surfaces are excluded unless explicitly approved.
- [x] Confirm no secrets, credentials, or live user config values appear in diffs or reports.

## Validation

- [x] Run `uv run wagents openspec validate`.
- [x] Run targeted `git diff --check` for release-owned paths.
- [x] Review child status JSON for all release lanes.
- [x] Run a lane-scoped code/doc review and address blockers.
- [x] Record skipped checks and why they are safe to defer.

## Documentation

- [x] Decide whether generated docs are regenerated now or deferred.
- [x] If regenerated, review generated docs separately from planning changes.
- [x] Ensure `planning/95-migration/50-release-notes.md` lists child lanes, commits, validation commands, exclusions, and known risks.

## Release Candidate Evidence

- [x] Stage with exact pathspecs.
- [x] Commit one logical release unit with a conventional commit message.
- [x] Confirm `git status --short --branch` shows only intended staged/committed changes affected by the release.
- [x] If creating a PR, include rollback and archive readiness sections.

## Post-Merge

- [x] Re-run `uv run wagents openspec validate` from merged `main`.
- [x] Confirm generated docs/instruction mirrors are either synchronized or explicitly deferred.
- [x] Confirm archive checklist is ready before moving OpenSpec changes.

## Archive Cleanup Commit Gate

The archive cleanup commit is verified by the current git commit, push, and CI evidence rather than pre-checked in this release-readiness document. Stage archive moves, synced specs, and release-evidence cleanup with exact pathspecs; commit them as one logical conventional commit; then re-run validation from committed `main` and verify CI after push.

Deferred runtime fixture work is tracked as follow-up validation evidence and no longer blocks the archived planning/control-plane change set.
