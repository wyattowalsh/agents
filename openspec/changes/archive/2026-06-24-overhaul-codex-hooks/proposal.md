# Proposal

## Problem

Repo-managed Codex hooks were still generated with an older, under-specified Codex hook shape. The live hooks lacked per-handler `timeout` and `statusMessage` metadata, the renderer only knew a subset of current Codex lifecycle events, and the research stop verifier needed to return the current Codex continuation shape.

## Intent

Bring Codex hook generation and research hook policy output in line with the current Codex hooks contract while preserving local hook entries that are not repo-managed.

## Scope

- Expand the Codex hook event mapping to the current supported lifecycle events.
- Render Codex command hook handlers with explicit seconds-based `timeout` values and optional `statusMessage` text.
- Preserve local, non-generated hook groups while replacing stale repo-generated `wagents-hook.py` groups during sync.
- Keep the repo-owned Codex config copy focused on managed config and avoid projecting local-only tool toggles.
- Add user-approved Codex defaults for post-edit quality context and stop-time truth gating.
- Update tests that lock Codex hook rendering and stop-continuation behavior.

## Out Of Scope

- Replacing the existing cross-harness hook registry format.
- Auto-adding additional researched hook candidates before user approval.
- Archiving the OpenSpec change before implementation and validation are complete.
- Reverting unrelated dirty worktree changes in MCPHub or harness config files.
