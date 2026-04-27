@/Users/ww/dev/projects/agents/instructions/global.md

# GitHub Copilot

Copilot-specific extension only. Keep shared cross-platform instructions in `global.md`.

## Fleet Planning

- All plans must be `/fleet`-optimized per `/orchestrator` for maximum efficiency and robustness.
- Default to the highest applicable `/orchestrator` tier; do not collapse parallelizable work into a single-session plan.
- Maximize independent subagent dispatch, preserve clear file ownership, and keep synthesis gated on all dispatched work completing.

## Fleet Model Policy

- Default to the globally managed stable profile: `gpt-5.4-mini`, low reasoning effort, `continueOnAutoMode`, `COPILOT_SUBAGENT_MAX_CONCURRENT=2`, and `COPILOT_SUBAGENT_MAX_DEPTH=1`.
- Use heavier models only when explicitly requested or when a bounded plan identifies a concrete need for deeper reasoning.
- Keep `/fleet` fan-out bounded. Prefer short, accountable waves over unbounded subagent trees; broad uncontrolled fan-out can trip Copilot API limits and transient backend retry loops.
