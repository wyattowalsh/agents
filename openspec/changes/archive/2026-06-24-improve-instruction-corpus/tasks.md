# Tasks

## OpenSpec

- [x] Add OpenSpec artifacts for this approved instruction-corpus change.
- [x] Add an OpenSpec requirement delta for instruction truth and secret-bypass safety.

## Implementation

- [x] Update `instructions/global.md` for safer precedence, trust boundaries, orchestration, git, commit, and docs lookup guidance.
- [x] Update `instructions/opencode-global.md` to remove persistent secret-bypass setup guidance.
- [x] Update `AGENTS.md` to match the instruction architecture and token-budget changes.
- [x] Regenerate repo-managed instruction surfaces with `uv run python scripts/sync_agent_stack.py --targets repo --apply`.

## Verification

- [x] Run sync drift, asset validation, OpenSpec validation, README freshness, stale include, and secret-bypass persistence checks.
- [x] Report unrelated pre-existing dirty worktree or validation drift separately from this implementation.
