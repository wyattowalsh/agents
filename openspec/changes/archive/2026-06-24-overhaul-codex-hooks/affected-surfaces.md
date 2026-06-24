# Affected Surfaces

## Owned

- `scripts/sync_agent_stack.py` - Codex hook rendering, event mapping, and sanitized Codex config generation.
- `hooks/wagents-hook.py` - Codex policy output for post-edit quality context, stop truth gating, and research stop continuation.
- `tests/test_sync_agent_stack.py` - Codex hook renderer regression coverage.
- `tests/test_wagents_hook.py` - Codex post-edit quality and stop verifier output coverage.
- `config/codex-config.toml` - repo-owned sanitized Codex config copy generated from sync logic.
- `openspec/changes/overhaul-codex-hooks/` - change-control artifacts for this work.

## Generated Or Live

- `~/.codex/hooks.json` - live Codex hook config updated by home sync; preserve non-generated local hook entries.
- `~/.codex/config.toml` - live Codex config updated by home sync; local extras are allowed there.

## Validation

- `uv run pytest tests/test_sync_agent_stack.py -k 'codex_hook or standard_hook_renderers or merge_codex_hooks or render_codex_config_enables_hooks_feature'`
- `uv run pytest tests/test_wagents_hook.py -k 'codex or stop_verifier'`
- `uv run wagents openspec validate`
- `uv run python scripts/sync_agent_stack.py --targets repo,home --check`
