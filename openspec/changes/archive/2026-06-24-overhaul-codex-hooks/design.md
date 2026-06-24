# Design

## Codex Renderer

Codex hook generation uses a dedicated `render_codex_hooks()` function. The
renderer accepts portable registry entries and emits Codex command handlers with
only current official fields:

- `type`
- `command`
- `timeout`
- `statusMessage`
- `commandWindows` when explicitly configured

The generic renderer remains responsible for Claude Code and Gemini CLI. Codex
merge behavior keeps local non-generated hooks and strips only generated
`wagents-hook.py` entries before appending refreshed managed hooks.

## Registry

The portable registry gains Codex entries for high-value defaults:

- session-start context,
- destructive shell guard,
- protected file guard,
- permission-request guard,
- post-tool verification context with lightweight post-edit quality checks,
- stop-time truth gate for final code-change claims.

Codex lifecycle events that do not yet have deterministic policies remain
renderable but disabled by omission from the default registry.

## Hook Runner

`hooks/wagents-hook.py` owns Codex JSON behavior for the new policies. The guard
policies inspect normalized tool payloads and deny only high-confidence unsafe
operations. Permission-request handling denies the same critical patterns and
otherwise returns no decision so Codex continues its normal approval flow.

Post-tool verification is context-only and does not mutate files. It runs only
lightweight checks on directly touched paths, such as `git diff --check`,
Python compile checks without `__pycache__` writes, and JSON/TOML parse checks.

The stop-time truth gate is conservative: it asks Codex to continue only when
the latest assistant message claims code or repository work changed but omits
validation evidence or an explicit note that validation was not run. Stop and
SubagentStop continuation uses `{"decision":"block","reason":"..."}`.

## Surface Discovery

Harness discovery reports both project and global Codex hook surfaces:

- `.codex/hooks.json`
- `~/.codex/hooks.json`

Global hooks are expected to be generated or merged by the sync workflow; project
hooks are observable when present.
