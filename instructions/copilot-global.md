@/Users/ww/dev/projects/agents/instructions/global.md

# GitHub Copilot

Copilot-specific extension only. Keep shared cross-platform instructions in `global.md`.

## Fleet Planning

- All plans must be `/fleet`-optimized per `/orchestrator` for maximum efficiency and robustness.
- Default to the highest applicable `/orchestrator` tier; do not collapse parallelizable work into a single-session plan.
- Maximize independent subagent dispatch, preserve clear file ownership, and keep synthesis gated on all dispatched work completing.

## Fleet Model Policy

- For GitHub Copilot CLI `/fleet` work, use **Claude Opus 4.6 with max thinking** for every non-trivial subagent, teammate, wave, and `/fleet` member.
- Use **Claude Sonnet 4.6 with max thinking** only for incredibly/extremely trivial `/fleet` subagents, such as deterministic single-file metadata edits, narrow read-only lookups, or obvious mechanical rewrites with no cross-file reasoning.
- If there is any ambiguity about whether `/fleet` work is trivial, default to **Claude Opus 4.6 with max thinking**.
- Never downgrade from Opus for cost or speed when the work requires judgment, debugging, architecture, cross-file reasoning, or multi-step synthesis.
