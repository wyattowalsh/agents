# Proposal

## Problem

OpenCode `openai/gpt-5.5` failures can look like model or plugin outages even when the active problem is a poisoned session replaying stale encrypted reasoning state. At the same time, the live TUI shortcut config had drifted to stale `keymap.sections` while current OpenCode uses `keybinds`.

## Intent

Lock the repo-managed OpenAI provider shape, document the session-poisoning recovery path, and migrate the live TUI shortcut config to the current schema.

## Scope

- Update `opencode.json` and OpenCode config generation to keep explicit `openai/gpt-5.5` provider options and build/plan defaults.
- Keep the TUI model picker useful by exposing supported provider variants while preserving build `high` and plan `xhigh` request behavior.
- Update live `~/.config/opencode/tui.json` to use `keybinds`.
- Document the session-local encrypted reasoning poisoning failure mode and recovery flow.
- Update targeted tests for the enforced provider shape.

## Out Of Scope

- Falling back from `openai/gpt-5.5`.
- Removing encrypted reasoning from healthy sessions.
- Introducing a repo-owned TUI config source file.
- Rewriting unrelated OpenCode plugin inventory or dirty worktree changes.
