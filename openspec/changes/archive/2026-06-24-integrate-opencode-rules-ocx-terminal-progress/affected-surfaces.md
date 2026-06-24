# Affected Surfaces

## Source Of Truth

- `opencode.json` — canonical repo-managed OpenCode runtime plugin array.
- `.opencode/PLUGINS.md` — installation and placement notes for OpenCode npm, local, and external/manual plugins.
- `AGENTS.md` — repo-wide OpenCode plugin policy.
- `instructions/opencode-global.md` — OpenCode-specific runtime guidance.
- `wagents/cli.py` — README generation source for OpenCode distribution wording.
- `tests/test_distribution_metadata.py` — fixture coverage for runtime plugin inclusion and OCX exclusion.
- `.opencode/ocx.jsonc` and `.ocx/receipt.jsonc` — existing OCX component manager surfaces, unchanged by this change.

## Generated Outputs

- `README.md` from `uv run wagents readme`.

## External Sources

- `https://github.com/frap129/opencode-rules` — npm package `opencode-rules`, latest verified as `0.6.4`.
- `https://github.com/kdcokenny/ocx` — npm package/CLI `ocx`, latest verified as `2.0.9`.
- `https://github.com/pedropombeiro/opencode-plugins/tree/main/packages/terminal-progress` — npm package `opencode-terminal-progress`, latest verified as `0.5.0`.

## Validation Commands

- `uv run wagents openspec validate --format json`
- `uv run pytest tests/test_distribution_metadata.py tests/test_sync_agent_stack.py`
- `uv run wagents validate`
- `uv run python skills/harness-master/scripts/discover_surfaces.py --repo-root . --level both --harness opencode`
- `uv run wagents readme --check`
- `ocx --version`
- `ocx verify`

## Review Notes

- Do not create OCX profiles or worktrees while validating this change.
- Do not add `ocx@latest` or `opencode-worktree@latest` to `opencode.json`.
