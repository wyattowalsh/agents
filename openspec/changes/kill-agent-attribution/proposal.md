# Change: kill-agent-attribution

## Why
Never sign commits with automated agent attribution trailers (Cursor Co-authored-by / Made-with).

## What Changes
- Extend `git_commit_push_guard` to deny Cursor attribution trailers in git commit commands.
- Keep FAIL_CLOSED registry wiring for `git-commit-push-guard`.
- Document never-sign parity in AGENTS/instructions (already present).

## Impact
- Hooks: pre-tool shell commit path
- Tests: policy module fixtures
