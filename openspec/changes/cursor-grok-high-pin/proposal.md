# Change: Cursor Grok 4.5 High Pin

## Why

Cursor custom agents are already overlay-pinned to `cursor-grok-4.5-high`, but soft
guidance still allowed Task omit/`inherit`/`*-fast`, home sync skipped or over-deleted
rules, home agents were unsynced, and OpenSpec still documented `model: inherit`. Force
High everywhere controllable so Explore/Task/subagents cannot silently fall to Fast.

## What Changes

- Flip `openspec/specs/cursor-harness` from `model: inherit` to `cursor-grok-4.5-high`.
- Require explicit High on every Task launch (no omit).
- Soft rule `.cursor/rules/cursor-models.mdc` always-on pin + ban list.
- Adapter default and managed-marker home agents under `~/.cursor/agents/`.
- Home sync: allowlisted rules copy (at least `cursor-models.mdc`) without orphan deletes.
- Hooks Phase A: `preToolUse` Task rewrite via `updated_input` (fail-open).
- Hooks Phase B: `subagentStart` allowlist deny for non-High models.
- Local app: CLI `exploreSubagentModel: inherit`; IDE picker Grok 4.5 High; never hand-edit live `state.vscdb`.

## Non-Goals

- Cloud Agent / dashboard / team admin / Bugbot / ACP model control.
- Inventing `settings.json` model keys or SQL writes to live `state.vscdb`.
- Dead `tooling-policy.json` `model_defaults.cursor` keys.
- Changing Grok Build / OpenCode / Codex model defaults.
