# Tasks

## OpenSpec

- [x] Add OpenSpec artifacts for this change.

## Implementation

- [x] Update Codex hook rendering to include the current Codex event set.
- [x] Render Codex command hooks with explicit timeout and status message metadata.
- [x] Keep Codex stop-verifier continuation output aligned with current Codex hook semantics.
- [x] Keep Codex hook registry policy IDs implemented in `hooks/wagents-hook.py`.
- [x] Add user-approved post-edit quality verification context for Codex.
- [x] Add user-approved stop-time truth gate for final code-change claims.
- [x] Keep the sanitized repo Codex config copy free of local-only tool toggles.
- [x] Report Codex project and global hook surfaces in harness discovery.
- [x] Preserve non-managed live Codex hooks while replacing generated `wagents-hook.py` entries.

## Documentation

- [x] Invoke docs-steward sync/maintain for generated docs artifacts.

## Verification

- [x] Run targeted sync-agent-stack hook tests.
- [x] Run targeted wagents hook policy tests.
- [x] Run targeted post-edit quality and stop truth-gate tests.
- [x] Run `uv run wagents validate`.
- [x] Run `uv run wagents hooks validate --format json`.
- [x] Run Codex config schema validation.
- [x] Run docs build under Node 24.
- [x] Run `uv run wagents openspec validate`.
- [x] Run repo sync drift check and apply isolated Codex hooks merge for affected live hooks.
- [x] Document unrelated full-home sync blocker from OpenCode config drift.
