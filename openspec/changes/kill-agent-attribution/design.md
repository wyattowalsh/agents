# Design: kill-agent-attribution

## Decision
Extend existing `evaluate_git_commit_push` rather than a new policy module.

## Rationale
Same registry key, same FAIL_CLOSED shell gate, one load path in wagents-hook.

## Trailer fingerprints
- `Co-authored-by: ... Cursor`
- `Made-with: Cursor`
- `Generated-by` / `Signed-off-by` with Cursor

## Non-goals
- Commit-msg file hooks for all harnesses (command-string gate covers agent shell commits)
- Blocking non-Cursor human trailers
