# Affected Surfaces

## New tracked source files

- `config/schemas/hook-registry.schema.json` — schema for the hook registry.
- `config/schemas/external-hooks-registry.schema.json` — schema for external hooks.
- `config/external-hooks-registry.json` — curated external hooks registry (Plannotator row).
- `wagents/hooks/__init__.py` — new package.
- `wagents/hooks/render.py` — shared hook renderer.
- `wagents/hooks/merge.py` — consolidated strip/merge helpers.

## Modified tracked source files

- `config/hook-registry.json` — adds `$schema` pointer only (no hook semantics change).
- `wagents/apm.py` — imports shared renderer; removes inline `_render_*_shape` bodies.
- `scripts/sync_agent_stack.py` — imports shared renderer and merge module; thin wrappers.
- `wagents/platforms/base.py` — imports `HOOK_COMMAND_MARKERS`, `strip_generated_hook_entries`, `merge_hook_groups` from `wagents/hooks/merge.py`.
- `tests/test_distribution_metadata.py` — adds two config/schema conformance pairs.

## Generated / downstream surfaces

- `.apm/hooks/*.json` — output is byte-stable in this change; no regeneration required.
- Local OpenSpec tool artifacts (`.claude`, `.cursor`, `.codex`, `.gemini`, `.opencode`, `.github`) — not committed.

## Out of scope surfaces (later gates)

- `wagents/platforms/cursor.py`, `claude.py`, `gemini.py`, `codex.py`, `grok.py`, `opencode.py`.
- `wagents/hooks/policies/`, `hooks/wagents-hook.py`.
- `config/plannotator-hooks.policy.json`, `config/cursor-global-hooks.json`.
- `docs/src/content/docs/hooks/`.
