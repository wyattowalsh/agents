## Summary

Drive the repository to public-release production readiness with strict local/CI
gate parity, fail-closed validation contracts, warning-free docs builds, public
path/secret hygiene, and classified local cleanup.

## Problem

The release surface currently has multiple blocking classes: failing tests,
lint/type diagnostics, docs build warnings, a fail-open OpenSpec wrapper path,
generated catalog path leakage risk, and unclassified ignored runtime/build
state. A one-pass validation check is not enough because generators and docs
commands can create fresh output after the first green run.

## Proposed Change

- Repair validation commands so malformed eval, hook, catalog, and OpenSpec
  states fail closed.
- Align local, CI, docs, package, catalog, and release validation commands.
- Ensure generated public docs and registries are public-safe and path-relative.
- Run focused gates first, then the full validation matrix until two consecutive
  clean runs have zero errors, warnings, leaks, and unclassified file noise.
- Classify ignored/local cleanup into removed, rehydratable, preserved, or
  approval-required buckets.

## Non-Goals

- Do not publish, tag, push, create commits, switch branches, or run live
  installs.
- Do not delete secrets, active runtime state, or user-owned local state without
  explicit maintainer approval.
- Do not hand-edit generated docs or registries except as generator output.
