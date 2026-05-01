# AI Instruction Sync Plan

## Objective

Keep agent-facing instructions aligned across harnesses while preserving each tool's idiosyncratic conventions.

## Source hierarchy

1. `instructions/global.md` — canonical cross-platform behavior.
2. Harness-specific instruction source files under `instructions/`.
3. Thin root wrappers: `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`.
4. Path-scoped rules/instructions under `.github/instructions`, `.cursor/rules`, `.claude/rules`.
5. Skills for situational workflows.

## Sync checks

- Root wrappers import or reference canonical source.
- Copilot instructions do not diverge from global rules except where Copilot requires different syntax.
- Long procedures move into skills.
- Harness-specific caveats are documented and scoped.
- Token budgets stay visible.

## Task graph requirement

Every instruction file must have a matching task node for audit, update, and CI validation.
