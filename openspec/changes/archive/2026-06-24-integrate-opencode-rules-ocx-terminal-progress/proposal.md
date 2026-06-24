# Proposal

## Problem

The requested OpenCode ecosystem tools have different integration models: `opencode-rules` and `opencode-terminal-progress` are npm runtime plugins, while OCX is a CLI/component manager. Treating all three as the same kind of plugin would risk incorrect `opencode.json` entries, undocumented rule-injection behavior, and accidental branch/worktree automation from OCX-managed components.

## Intent

Add the runtime plugins through the repo-managed OpenCode plugin array, keep OCX documented and verified as a CLI/component manager, and update docs/tests so future syncs preserve those boundaries.

## Scope

- Add `opencode-rules@latest` to the repo-managed OpenCode runtime plugin list.
- Add `opencode-terminal-progress@latest` to the repo-managed OpenCode runtime plugin list.
- Keep OCX out of `opencode.json` and document it as CLI/component-managed.
- Document rule-injection cautions, terminal progress behavior, and OCX verification/update commands.
- Add tests that enforce the runtime plugin inclusions and OCX exclusion.

## Out Of Scope

- Creating, switching, or deleting branches/worktrees.
- Creating scheduler jobs or OCX profiles.
- Installing or updating OCX-managed components unless separately approved.
- Moving global OpenCode rule files into this repository.
- Reverting unrelated dirty worktree changes.

## Risks

- `opencode-rules` can duplicate always-loaded instructions if broad unconditional rules are added.
- `opencode-rules` depends on experimental OpenCode hook APIs, so runtime upgrades may need compatibility checks.
- `opencode-terminal-progress` writes terminal control sequences, though upstream no-ops in unsupported terminals and supports `OPENCODE_TERMINAL_PROGRESS=0`.
- OCX-managed worktree components can create branch-backed sessions, so setup must not trigger worktree automation.
