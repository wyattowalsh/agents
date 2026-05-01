# Affected Surfaces

## Source Of Truth

- `opencode.json` — repo-managed OpenCode runtime plugin mirror.
- `instructions/opencode-global.md` — OpenCode-specific policy for model-neutral config, plugin placement, telemetry secrets, and scheduler/auth/workflow guardrails.
- `opencode-setup/INSTALL_MANIFEST.md` — machine install inventory and verification notes.
- `opencode-integration-plan-extended.md` — active OpenCode integration evolution record.
- `tests/test_distribution_metadata.py` — regression coverage for bundle and OpenCode plugin metadata.
- `openspec/changes/integrate-opencode-plugins/` — change-control artifacts for this work.

## Generated Outputs

- None expected.
- Run validation to confirm README/docs generation is not required by this change.

## Downstream Agent Artifacts

- `~/.config/opencode/opencode.json` — live user runtime OpenCode config.
- `~/.config/opencode/tui.json` — live user OpenCode TUI config.
- OpenCode npm plugin cache under `~/.cache/opencode/packages/` may refresh automatically on startup.

## Tests

- `tests/test_distribution_metadata.py`

## Validation Commands

- `jq empty opencode.json ~/.config/opencode/opencode.json ~/.config/opencode/tui.json`
- `uv run pytest tests/test_distribution_metadata.py`
- `uv run wagents validate`
- `uv run wagents openspec validate`
- `git diff --check`
- `opencode --print-logs --log-level DEBUG models anthropic`
