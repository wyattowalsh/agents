# Tasks

## OpenSpec

- [x] Add OpenSpec artifacts for this change.

## OpenCode Config

- [x] Add `opencode-rules@latest` to `opencode.json`.
- [x] Add `opencode-terminal-progress@latest` to `opencode.json`.
- [x] Preserve OCX as CLI/component-managed rather than a runtime plugin.

## Docs And Policy

- [x] Update `.opencode/PLUGINS.md` with npm plugin and OCX guidance.
- [x] Update `AGENTS.md` OpenCode plugin policy.
- [x] Update `instructions/opencode-global.md` OpenCode-specific rules.
- [x] Update README distribution wording for OpenCode runtime/OCX behavior.

## Tests

- [x] Update distribution metadata tests for new runtime plugins.
- [x] Add or update tests that ensure OCX is excluded from runtime plugin config.

## Verification

- [x] Run OpenSpec validation for this change.
- [x] Run targeted distribution metadata tests.
- [x] Run `uv run wagents validate`.
- [x] Run OpenCode harness surface discovery.
