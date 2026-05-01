# Multiagent UI Pattern Ledger

## Scope

This ledger captures external UI and multiagent coordination patterns as requirements input only. It does not vendor UI code or add runtime dependencies.

## Pattern Classes

| Pattern | Use | Risk |
| --- | --- | --- |
| Task board | Track child lanes, subagents, status, and blockers. | Can overstate completion if task semantics are vague. |
| Run graph | Show dependencies between prompts, tools, files, validations, and commits. | Can expose sensitive file or tool metadata without redaction. |
| Review queue | Surface findings, severity, owner, and resolution state. | Needs clear source trace to avoid stale comments. |
| Support matrix | Show harness tiers and evidence. | Must not collapse desktop/web/CLI/editor variants. |
| Timeline replay | Debug agent decisions and tool calls. | Requires retention and privacy controls. |

## Adoption Risks

- External dashboards can introduce unreviewed auth, network, or telemetry behavior.
- UI state can imply support tiers before fixtures pass.
- Screenshots and traces may include secrets or private repo paths.

## Recommended Abstractions

- `ChangeRun`: one OpenSpec parent or child execution.
- `LaneStatus`: task completion, validation state, and owner.
- `AgentDispatch`: subagent prompt, result, and review status.
- `ValidationGate`: command, result, and artifact path.
- `SurfaceClaim`: harness, tier, evidence, and blind spots.

Coordinate implementation with C05 so UX contracts and dashboard abstractions stay aligned.
