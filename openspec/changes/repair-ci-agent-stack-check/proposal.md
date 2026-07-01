## Summary

Repair CI validation so workflow linting and agent-stack sync checks run in
repository-safe mode.

## Problem

The CI workflow currently calls `scripts/check_agent_stack.py`, which checks
`--targets all` and can inspect user-home harness config. That is appropriate
for local maintainer drift checks, but it is not CI-safe. A previous duplicate
workflow job also risked shadowing the actionlint-installing workflow lint job.

## Proposed Change

- Run agent-stack validation in CI with `scripts/sync_agent_stack.py --check --targets repo`.
- Keep local full-stack validation available through `scripts/check_agent_stack.py`.
- Ensure the workflow lint job is represented once and installs pinned
  `actionlint` before invoking `make ci-check`.

## Non-Goals

- Do not change local home-config sync semantics.
- Do not run home-target agent-stack sync, live skill installs, branch
  operations, commits, resets, or stashes.
