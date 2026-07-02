# Worktree Parallel Agents Runbook

Run independent agent workstreams in isolated git worktrees without colliding on the same branch checkout.

## When to Use

- Multiple subagents need write access to different file sets at the same time.
- Long-running validation or docs builds should not block the primary session worktree.
- OpenSpec or IDEAS waves assign parallel owners with explicit file boundaries.

## Prerequisites

- Clean understanding of file ownership per workstream (orchestrator conflict check).
- User explicitly requested worktrees or branches (repo git branch policy).
- Sufficient disk space for additional checkouts.

## Workflow

### 1. Plan ownership

Document which agent owns which paths before creating worktrees. Same-file edits must stay sequential.

### 2. Create worktrees (explicit user intent)

```bash
git worktree add ../agents-w12-a -b feat/w12-skills
git worktree add ../agents-w12-b -b feat/w12-agents
```

Use sibling paths outside the primary clone when tooling expects separate roots (for example Cursor `move_agent_to_root`).

### 3. Bootstrap each worktree

```bash
cd ../agents-w12-a
uv sync
uv run wagents validate
```

Copy or symlink local-only secrets only through user-owned paths — never commit `.env*` files.

### 4. Dispatch parallel agents

- Point each harness session at its worktree root.
- Run scoped validation in each tree: `uv run wagents validate`, skill `scripts/check.py`, targeted pytest.
- Parent session synthesizes results; only one worktree merges at a time.

### 5. Merge and retire

```bash
git -C ../agents-w12-a push -u origin feat/w12-skills
gh pr create ...
git worktree remove ../agents-w12-a
```

Resolve conflicts in the primary clone; re-run full validate matrix before merge.

## Safety Rules

1. Do not create worktrees or branches unless the user explicitly asked.
2. Never force-push shared branches.
3. Keep dirty state in the primary worktree — do not use worktrees to hide uncommitted work.
4. Quarantine failed parallel runs instead of copying partial artifacts across trees by hand.

## Related

- `/orchestrator` — decomposition, conflict check, dispatch tracking
- `agents/triage-lead.md` — severity and ownership routing
- `docs/runbooks/asset-authoring-workflow.md` — validate → docs generate loop
