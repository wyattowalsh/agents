# CLI Output Contracts

## Scope

This document defines user-facing and machine-readable output contracts for future `wagents` UX work. It does not change CLI implementation in this pass.

## Human Output

Human output should be concise and grouped by action:

- What changed.
- What validation ran.
- What is blocked or deferred.
- What command to run next.

Avoid mixing unrelated dirty worktree entries into lane summaries unless they block the current lane.

## JSON Output

Machine-readable commands should return:

- `status`: `ok`, `blocked`, or `failed`.
- `items`: array of typed records.
- `summary`: counts and high-level state.
- `warnings`: non-fatal issues.
- `next_actions`: optional structured follow-ups.

JSON must not contain secrets, raw env values, cookies, or private credential paths beyond redacted labels.

## Dashboard Information Architecture

Dashboards should group by:

- Change and child lane.
- Harness/support tier.
- Validation gate.
- Dirty/generated/shared surface status.
- Review findings and owner.
