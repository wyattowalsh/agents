## Summary

Add `grok-delegate` as the canonical first-party skill for cross-harness orchestration of Grok Build via native CLI surfaces only (headless `-p`, session resume, leader, worktrees, ACP stdio). Extend `wagents grok doctor` with `--format json`.

## Why OpenSpec

This adds a public skill, extends wagents CLI output shape, updates orchestrator/harness-master cross-links, and affects multi-harness sync projections.

## Problem

Codex, OpenCode, and other parent harnesses can bash-invoke `grok`, but the repo lacks a portable contract for task-graph dispatch, session tune loops, parallel wave ownership, and pre-flight health checks. OpenCode has a custom `bin/oc` wrapper; Grok Build already ships headless, leader, and ACP modes that should be used directly.

## Proposed Change

- Add `skills/grok-delegate/` with wave DAG references, session ledger schema, safety matrix, and native command templates.
- Add `wagents grok doctor --format json` using structured checks in `wagents/grok_doctor.py`.
- Cross-link from `orchestrator`, `harness-master`, and `instructions/global.md`.

## Non-Goals

- No `bin/gk`, FastMCP control server, or `wagents grok run` shim.
- No live `skills sync --apply` in this change record.
- No A2A Agent Cards.