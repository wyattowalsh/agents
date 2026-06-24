# Design

## Approach

Use the smallest source-level changes that remove unsafe or stale instructions while preserving the repo's existing progressive-disclosure model: edit canonical shared policy once, edit the OpenCode overlay where behavior is platform-specific, then regenerate downstream mirrors.

## Decisions

- Replace automatic commit guidance with explicit-user-request commit guidance because commits are durable git operations and current agent runtime policy requires explicit user intent.
- Add a trust-boundary section to the canonical instructions so external pages, tool output, generated files, and fetched docs cannot override higher-priority instructions or induce secret disclosure.
- Keep orchestration guidance, but make subagent/team fan-out conditional on independent workstreams and conflict checks rather than an unconditional team default.
- Remove the unresolved `@RTK.md` include instead of creating a compatibility placeholder because no source file exists and no persisted consumer requires that include.
- Change OpenCode secret bypass guidance from persistent shell-profile setup to one-shot, scoped environment usage with immediate cleanup.

## Alternatives Rejected

- Add a stub `RTK.md`: rejected because it preserves an unexplained include rather than removing stale instruction debt.
- Hand-edit generated Codex/Copilot files: rejected because generated surfaces should be refreshed from canonical sources.
- Change `scripts/sync_agent_stack.py` preemptively: rejected unless regeneration proves a generator defect.
