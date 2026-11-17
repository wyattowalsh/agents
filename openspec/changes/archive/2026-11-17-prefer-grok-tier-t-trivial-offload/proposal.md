# Proposal

## Why

The existing Grok delegation policy describes Tier-T trivial offload as optional, so parent agents can ignore eligible bounded leaves even when Grok is available. The desired behavior is stronger but still narrow: use Grok as much as practical for trivial subtasks, while preventing Grok from taking broad, risky, overlapping, or synthesis-owning work.

## What Changes

- Strengthen global and harness instruction surfaces from optional Tier-T language to default-when-eligible language.
- Update `grok-delegate` and `orchestrator` guidance so decomposition includes a Tier-T eligibility pass.
- Add fallback semantics: after the first native Tier-T `grok -p` dispatch failure in a parent work item, stop Tier-T for that work item and continue locally.
- Add eval coverage for underuse, overuse, failed dispatch fallback, and excluded task classes.

## Impact

Parent harnesses should more consistently use `/grok-delegate trivial` for bounded leaves when fast preflight and `grok-auth-expiry` pass. The parent remains responsible for safety checks, synthesis, and verification.

## Scope

- Instruction surfaces, Grok delegate skill text, orchestrator guidance, evals, and this OpenSpec delta.

## Out Of Scope

- Hooks or hard enforcement for Tier-T routing.
- Live `skills sync --apply`, home sync, branch changes, commits, or pushes.
- New Grok wrappers, MCP servers, or nested Grok orchestration.

## Risks

- Stronger wording could cause over-delegation. Mitigate with explicit ineligible cases and evals for broad, overlapping, destructive, production, git-push, and secret-reading tasks.
- Native Grok can fail after fast preflight passes. Mitigate with the first-dispatch fallback rule.
