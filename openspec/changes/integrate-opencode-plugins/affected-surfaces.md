# Affected Surfaces

## Source Of Truth

- `opencode.json` — repo-managed OpenCode runtime plugin mirror.
- `instructions/opencode-global.md` — OpenCode-specific policy for model-neutral config, plugin placement, telemetry secrets, and scheduler/auth/workflow guardrails.
- `opencode-setup/INSTALL_MANIFEST.md` — machine install inventory and verification notes.
- `.opencode/PLUGINS.md` — repo-local OpenCode plugin installation notes.
- `.opencode/ocx.jsonc` and `.ocx/receipt.jsonc` — OCX component config and integrity receipt for KDCO worktree support.
- `.opencode/plugin/worktree.ts`, `.opencode/plugin/worktree/`, and `.opencode/plugin/kdco-primitives/` — OCX-installed worktree component files.
- `.opencode/package.json` — repo-local plugin dependency manifest for OCX-installed components.
- `wagents/cli.py` and `wagents/site_model.py` — generated README/docs distribution text sources.
- `tests/test_distribution_metadata.py` — regression coverage for bundle and OpenCode plugin metadata.
- `openspec/changes/integrate-opencode-plugins/` — change-control artifacts for this work.

## Generated Outputs

- `README.md` from `uv run wagents readme`.
- Generated docs data may change if unrelated dirty skill assets exist; keep those unrelated generated changes out of this commit unless explicitly requested.

## Downstream Agent Artifacts

- `~/.config/opencode/opencode.json` — live user runtime OpenCode config.
- `~/.config/opencode/tui.json` — live user OpenCode TUI config.
- `~/.wakatime.cfg` — user-owned WakaTime credential config; credentials are not copied into repo-managed files.
- `~/.config/opencode/commands/` — Plannotator may copy slash command definitions during package install.
- OpenCode npm plugin cache under `~/.cache/opencode/packages/` may refresh automatically on startup.

## Tests

- `tests/test_distribution_metadata.py`

## Validation Commands

- `jq empty opencode.json ~/.config/opencode/opencode.json ~/.config/opencode/tui.json .opencode/ocx.jsonc .ocx/receipt.jsonc`
- `uv run pytest tests/test_distribution_metadata.py`
- `uv run wagents validate`
- `uv run wagents openspec validate`
- `ocx --version`
- `git diff --check`
- `opencode models anthropic`
