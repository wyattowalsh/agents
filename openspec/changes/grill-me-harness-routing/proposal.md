# Proposal

## Why

Harness agents batch clarification questions but rarely invoke `/grill-me` for user-pivotal plan and design uncertainty. The curated skill is installed but weakly discoverable and not wired into canonical instruction policy.

## What Changes

- Add Depth routing to `instructions/global.md` Clarification Gate with pivotal-user-input heuristic.
- Harmonize planner, orchestrator, researcher agents and orchestrator/research/new-project/openspec skills.
- Enrich grill-me catalog authoring; add Grok repo overlay; generalize Grok skill overlay sync.
- Add policy parity tests and regenerate harness instruction mirrors.

## Impact

Agents proactively route user-pivotal uncertainty to `/grill-me` without requiring explicit "grill me" keyword. Batched MCQ and codebase-first exploration remain for other cases.

## Out Of Scope

- Vendoring grill-me into `skills/`
- Hook-based enforcement
- Live `wagents skills sync --apply`