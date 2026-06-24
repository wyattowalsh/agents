# Design

## Approach

Add the rule at the canonical source, immediately after `Search & Match Discipline` and before `Clarification Gate`. This location keeps compatibility decisions adjacent to evidence-gathering rules and before the general question-asking policy.

## Instruction Text

```markdown
## Compatibility Discipline

- Default to clean current-state implementations. Treat current code plus the user's request as the source of truth; version control is the rollback path for unshipped behavior.
- Do not add legacy, migration, fallback, alias, dual-path, or compatibility code unless explicitly requested or required by concrete evidence of persisted data, deployed consumers, public APIs/file formats, or documented rollout/rollback needs.
- If that evidence is plausible but missing, ask one concise question before adding compatibility logic; otherwise omit it.
```

## Propagation Model

Use the existing sync stack. `instructions/opencode-global.md` imports `instructions/global.md`, repo `opencode.json` references both `AGENTS.md` and `instructions/opencode-global.md`, and the home sync writes OpenCode instruction paths from the canonical sources. Other supported harnesses receive the change through their existing generated bridges, symlinks, or home instruction files.

## Alternatives Rejected

- Edit every harness instruction directly: rejected because generated surfaces must come from canonical sources and sync scripts.
- Add a long policy section with examples: rejected because the user approved a shorter instruction and the rule should stay easy to apply.
- Add compatibility enforcement hooks now: rejected because the request is for instruction behavior, not deterministic validation behavior.

## Compatibility Notes

This change intentionally reduces default compatibility logic. Compatibility remains allowed when explicitly requested or required by concrete evidence of persisted data, deployed consumers, public APIs/file formats, or documented rollout/rollback needs.
