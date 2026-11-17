# Tasks: add-cursor-plannotator-hooks

## W1 OpenSpec

- [x] Proposal / design / affected-surfaces / validation-matrix / tasks
- [x] Delta specs: cursor-harness, docs-instructions, repo-sync
- [x] Append living specs
- [x] OpenSpec validate `--strict`

## W2 Implementation

- [x] `[P]` Shim `scripts/cursor/plannotator-plan-hook.py`
- [x] `[P]` `config/cursor-global-hooks.json` CreatePlan / SwitchMode template
- [x] Render placeholder substitution + home path helper
- [x] Cursor `sync_home` copy + merge gated on `grok_plannotator_hooks`
- [x] Merge heuristic for stale ExitPlanMode / raw-plannotator rows
- [x] `wagents cursor-cli plannotator sync|install`
- [x] Doctor warn-only checks

## W3 Docs / registries

- [x] `[P]` external-hooks-registry + hook-surface-registry
- [x] `[P]` AGENTS.md, cursor-cli overlay, harness-master, plannotator.mdx, README CLI ref
- [x] `uv run wagents web generate --no-installed` / `uv run wagents readme` if those surfaces change

## W4 Tests

- [x] Shim, render/merge, home sync skip, doctor
- [x] ruff / format / ty / pytest / validate / openspec
