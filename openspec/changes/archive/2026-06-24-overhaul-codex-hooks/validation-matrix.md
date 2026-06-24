# Validation Matrix

| Surface | Command | Expected Result |
| --- | --- | --- |
| Codex hook renderer tests | `uv run pytest tests/test_sync_agent_stack.py -k 'codex_hook or standard_hook_renderers or merge_codex_hooks or render_codex_config_enables_hooks_feature'` | Codex event mapping, metadata, hook merge, and hooks feature rendering pass. |
| Hook policy tests | `uv run pytest tests/test_wagents_hook.py -k 'codex or stop_verifier'` | Codex denial, post-edit quality, and stop-continuation output stay schema-compatible. |
| OpenSpec artifacts | `uv run wagents openspec validate` | OpenSpec changes and specs validate. |
| Repo sync drift | `uv run python scripts/sync_agent_stack.py --targets repo --check` | Repo-generated surfaces are current. |
| Live Codex hooks | `uv run python - <<'PY' ... s.merge_codex_hooks(s.SyncContext(apply=True), s.load_hook_registry()) ... PY` | Live `~/.codex/hooks.json` is updated without touching unrelated OpenCode home config. |

## Known Sync Blocker

The broad home sync command `uv run python scripts/sync_agent_stack.py --targets repo,home --check` is currently blocked by unrelated OpenCode local config drift. It refuses to update `~/.config/opencode/opencode.json` because sync would remove existing local model metadata under `$.provider.openai.models[...]`. This change therefore validates repo sync with `--targets repo --check` and applies only the Codex hook merge path for `~/.codex/hooks.json`.
