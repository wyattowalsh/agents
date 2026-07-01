# Affected Surfaces

## Repo-Owned Source

- `config/rtk-integration.json` - RTK fleet policy, harness tiers, commands, and non-goals.
- `wagents/rtk.py` - RTK doctor/sync/gain implementation.
- `wagents/cli.py` - Typer registration for `wagents rtk`.
- `wagents/self_cmd.py` - non-fatal `rtk` row in `wagents self doctor`.
- `hooks/wagents-hook.py` - research-to-implementation handoff behavior.

## Tests

- `tests/test_rtk_cli.py` - RTK policy, doctor, and sync tests.
- `tests/test_wagents_hook.py` - research hook handoff regression coverage.
- `tests/test_wagents_self.py` - self doctor RTK row.

## OpenSpec

- `openspec/changes/integrate-rtk-harness-fleet/*`
- `openspec/changes/integrate-rtk-harness-fleet/specs/downstream-tooling/spec.md`

## Local User-Owned Surfaces Not Edited

- `~/.claude/RTK.md`, `~/.claude/CLAUDE.md`, and `~/.claude/settings.json`
- `~/.cursor/hooks.json`
- `~/.config/opencode/plugins/rtk.ts`
- `~/.codex/RTK.md` and `~/.codex/AGENTS.md`
- `~/.gemini/hooks/` and `~/.gemini/settings.json`
- `~/.copilot/hooks/`
- `~/.grok/hooks/`

## Generated Surfaces

No generated docs or README surfaces are required for this scaffold. If maintainers decide to publish a public RTK catalog/docs row, use `uv run wagents docs generate` and `uv run wagents readme` in a follow-up.
