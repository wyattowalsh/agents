# Affected Surfaces

## Source Of Truth

- `opencode.json` — repo-managed OpenCode runtime plugin mirror.
- `instructions/opencode-global.md` — OpenCode-specific policy for model-neutral config, plugin placement, telemetry secrets, and scheduler/auth/workflow guardrails.
- `opencode-setup/INSTALL_MANIFEST.md` — machine install inventory and verification notes.
- `opencode-integration-plan-extended.md` — active OpenCode integration evolution record.
- `opencode-integration-plan.md` — condensed OpenCode integration summary.
- `.opencode/PLUGINS.md` — repo-local OpenCode plugin installation notes.
- `wagents/cli.py` and `wagents/site_model.py` — generated README/docs distribution text sources.
- `tests/test_distribution_metadata.py` — regression coverage for bundle and OpenCode plugin metadata.
- `openspec/changes/integrate-opencode-plugins/` — change-control artifacts for this work.

## Generated Outputs

- `README.md` from `uv run wagents readme`.
- Generated docs data may change if unrelated dirty skill assets exist; keep those unrelated generated changes out of this commit unless explicitly requested.

## Downstream Agent Artifacts

- `~/.config/opencode/opencode.json` — live user runtime OpenCode config.
- `~/.config/opencode/tui.json` — live user OpenCode TUI config.
- `~/.config/opencode/commands/` — Plannotator may copy slash command definitions during package install.
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
