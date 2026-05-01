# AI Instruction Sync Plan

## Canonical Sources

- Repo policy and asset format truth lives in `AGENTS.md` and imported instruction sources.
- Cross-platform behavior lives in `instructions/global.md`.
- Platform-specific behavior lives in `instructions/<platform>-global.md`.
- Harness configuration truth lives in registries and canonical config files, not generated bridge files.

## Bridge Surfaces

| surface | rule |
|---|---|
| `CLAUDE.md` | Generated or bridged from canonical instructions; do not hand-edit during child lanes. |
| `GEMINI.md` | Generated or bridged from canonical instructions; do not hand-edit during child lanes. |
| `.github/copilot-instructions.md` | Generated bridge surface; update only through instruction sync. |
| `.opencode/` generated skills or commands | Local generated support surface unless explicitly promoted. |

## Sync Rules

- Child lanes write instruction fragments under their allowed planning paths.
- C08 consolidates fragments into canonical instruction updates after schema and registry freeze.
- C08 must preserve platform-specific overrides, especially model-neutral OpenCode policy and plugin placement rules.
- Local user-owned harness settings must be preserved during sync; generated files must not overwrite secrets or local-only runtime choices.
- Any final sync that touches `README.md`, `AGENTS.md`, `CLAUDE.md`, or `GEMINI.md` requires explicit scheduling because those files are shared conflict surfaces.

## Validation

- `uv run wagents openspec validate` checks OpenSpec consistency.
- `uv run wagents readme --check` detects stale README generation without editing it.
- Docs generation commands must be run only when generated docs are intentionally scheduled.
