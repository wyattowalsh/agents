# Affected Surfaces

## Source of truth

- `config/cursor-global-hooks.json` — Cursor-native CreatePlan / SwitchMode template
- `scripts/cursor/plannotator-plan-hook.py` — home-copied fail-open shim
- `wagents/hooks/render.py` — placeholder substitution for the home shim path
- `wagents/hooks/merge.py` — replace stale ExitPlanMode / raw-binary Plannotator rows
- `wagents/platforms/cursor.py` — copy shim; merge only when Plannotator hooks are enabled
- `wagents/cli.py` — `wagents cursor-cli plannotator sync|install`
- `wagents/cursor_cli_doctor.py` — warn-only binary / hooks / shim checks
- `config/external-hooks-registry.json`
- `config/hook-surface-registry.json`
- `openspec/specs/cursor-harness/spec.md`
- `openspec/specs/docs-instructions/spec.md`
- `openspec/specs/repo-sync/spec.md`

## Instructions and maintainer docs

- `AGENTS.md` Plannotator matrix and Cursor editor / CLI rows
- `instructions/cursor-cli-global.md`
- `docs/src/content/docs/harness-config/plannotator.mdx`
- `skills/harness-master/SKILL.md`
- `docs/src/authoring/skills/harness-master.mdx`
- `skills/harness-master/references/harness-surfaces.md`
- `platforms/cursor-cli/README.md`
- `wagents/docs.py` CLI reference

## Generated (after authoring edits)

- `uv run wagents web generate --no-installed`
- `uv run wagents readme`

## Tests

- `tests/test_plannotator_cursor_plan_hook.py` (new)
- `tests/hooks/test_render_cursor.py`
- `tests/hooks/test_merge.py`
- `tests/test_sync_agent_stack.py`
- `tests/test_cursor_home_sync_pin.py`
- `tests/test_cursor_cli_doctor.py`

## Out of scope / do not edit

- Project `.cursor/hooks.json` (fleet hooks only; no Plannotator)
- `config/plannotator-hooks.policy.json` (Grok / Claude nested policy)
- Live `~/.cursor/hooks.json` apply during this change (operator-approved later)
