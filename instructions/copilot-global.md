@/Users/ww/dev/projects/agents/instructions/global.md

# GitHub Copilot

Copilot-specific extension only. Keep shared cross-platform instructions in `global.md`.

## Fleet Planning

- All plans must be `/fleet`-optimized per `/orchestrator` for maximum efficiency and robustness.
- Default to the highest applicable `/orchestrator` tier; do not collapse parallelizable work into a single-session plan.
- Maximize independent subagent dispatch, preserve clear file ownership, and keep synthesis gated on all dispatched work completing.

## Fleet Model Policy

- Default to the globally managed profile: `gpt-5.4`, high reasoning effort, `continueOnAutoMode=false`, and no explicit `COPILOT_SUBAGENT_MAX_CONCURRENT` or `COPILOT_SUBAGENT_MAX_DEPTH` caps.
- Use heavier or lighter models only when explicitly requested or when a bounded plan identifies a concrete need.
- Keep `/fleet` dispatch accountable. Do not invent artificial fan-out limits in instructions unless the user asks for them.
