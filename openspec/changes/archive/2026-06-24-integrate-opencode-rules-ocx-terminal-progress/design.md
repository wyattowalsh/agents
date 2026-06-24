# Design

## Integration Model

`opencode.json` remains the canonical project surface for OpenCode runtime npm plugins. Runtime plugin specs must use `@latest` so OpenCode's package installer resolves the newest published package during refresh.

OCX remains outside the runtime plugin array because it is an extension manager that installs or verifies copied components under `.opencode/` and receipts under `.ocx/`. Existing KDCO worktree component files and receipt hashes remain unchanged unless a separate component-update task is approved.

## Rule Injection Policy

`opencode-rules` should load only rules that are more specific than the always-loaded repo instructions. Prefer conditional rules using `globs`, `keywords`, `tools`, `command`, `project`, `branch`, `os`, `ci`, or `match`. Broad always-on rules should stay in `AGENTS.md` or `instructions/opencode-global.md` unless they are intentionally user-local.

## Terminal Progress Policy

`opencode-terminal-progress` is safe as a runtime plugin because it auto-detects supported terminals and is a no-op elsewhere. The repo should document the user-owned opt-out `OPENCODE_TERMINAL_PROGRESS=0` instead of setting it by default.

## Validation

Tests should verify:

- required runtime plugins are present in `opencode.json`
- runtime plugin specs use `@latest`
- TUI-only plugins stay out of `opencode.json`
- OCX and OCX-managed package names stay out of `opencode.json`
- existing OCX receipt files remain tracked and hash-verified
