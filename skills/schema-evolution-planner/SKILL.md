---
name: schema-evolution-planner
description: >-
  Plan zero-downtime schema changes across code, data backfills, and cutovers.
  Use for expand-contract database changes. NOT for fresh schema design or DBA
  ops.
argument-hint: "<mode> [change]"
license: MIT
metadata:
  author: wyattowalsh
  version: "1.0"
---

# Schema Evolution Planner

Plan safe, staged database schema changes across application code, backfills,
and cutovers.

**Scope:** Expand-contract and compatibility planning for live systems. NOT for
greenfield schema design (database-architect) or DBA operations.

## Canonical Vocabulary

| Term | Definition |
|------|------------|
| **expand** | Additive schema change compatible with existing code |
| **backfill** | Data migration that populates new structures from old data |
| **dual-write** | Temporarily writing old and new representations |
| **dual-read** | Temporarily reading from both old and new representations |
| **cutover** | The point where traffic or logic switches to the new path |
| **contract** | Removal of deprecated schema after compatibility window closes |
| **compatibility window** | Period where old and new code must both work |
| **invariant** | Condition that must remain true during migration |
| **shadow column** | New field added beside the old field during migration |
| **rollback point** | Last safe state that can be restored without data loss |

## Dispatch

| $ARGUMENTS | Mode |
|------------|------|
| `plan <change>` | Build the full migration sequence |
| `review <migration or rollout>` | Audit an existing evolution plan |
| `backfill <change>` | Design the data backfill strategy |
| `cutover <change>` | Plan read or write switchover |
| `deprecate <change>` | Plan the contract and removal stage |
| Natural language about zero-downtime schema changes | Auto-detect the closest mode |
| Empty | Show the mode menu with examples |

## Mode Menu

| # | Mode | Example |
|---|------|---------|
| 1 | Plan | `plan rename users.username to handle` |
| 2 | Review | `review migration plan for orders status enum change` |
| 3 | Backfill | `backfill new account_id on invoices` |
| 4 | Cutover | `cutover reads to new customer_profile table` |
| 5 | Deprecate | `deprecate legacy address columns` |

## When to Use

- Renaming columns or tables in a live system
- Splitting or merging tables without downtime
- Adding required fields to existing tables
- Introducing new identifiers or foreign keys gradually
- Coordinating schema changes with multiple application deploys

## Instructions

### Mode: Plan

1. Identify the current read paths, write paths, downstream consumers, and deployment order constraints.
2. Classify the change: rename, type change, split, merge, constraint hardening, or deletion.
3. Write an expand-contract sequence with explicit checkpoints: expand, deploy compatibility code, backfill, validate invariants, cutover, then contract.
4. Define the compatibility window and what old and new code must tolerate during it.
5. Name the invariants that must be measured before moving to the next phase.

### Mode: Review

1. Read the migration plan, migration files, and any rollout notes.
2. Check for hidden destructive steps, missing compatibility windows, or missing rollback points.
3. Flag assumptions about data quality, backfill runtime, and consumer readiness.
4. Rank findings by severity.

### Mode: Backfill

1. Define the source of truth and target population logic.
2. Make the backfill idempotent and chunkable.
3. Specify batching strategy, retry behavior, progress tracking, and reconciliation checks.
4. Decide whether dual-write is required while the backfill runs.

### Mode: Cutover

1. Separate write cutover from read cutover when they do not need to happen together.
2. Define the exact success checks before switching traffic or logic.
3. Keep a rollback point until the new path is proven stable.

### Mode: Deprecate

1. Verify no live code, jobs, or consumers still depend on the old structure.
2. Remove writes first, then reads, then the deprecated schema.
3. Record the evidence that the compatibility window is closed.

## Output Requirements

- Every plan must include expand, compatibility, validation, cutover, and contract stages.
- State the invariants to check between stages.
- Name the rollback point and the evidence needed to advance.

## Critical Rules

1. Never remove or repurpose a live field before the compatibility window closes.
2. Every backfill must be idempotent and restartable.
3. Cutovers must define success and abort criteria in advance.
4. Destructive changes belong only in the contract stage.
5. If the change is really a fresh schema design problem, route it to database-architect.

## Scope Boundaries

**IS for:** zero-downtime renames, splits, merges, backfills, staged cutovers, compatibility sequencing.

**NOT for:** greenfield schema modeling, query tuning, or database administration.
