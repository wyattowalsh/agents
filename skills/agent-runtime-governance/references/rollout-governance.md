# Agent Runtime Rollout Governance

Use this reference when a new or changed agent workflow can affect live users,
external accounts, credentials, deployments, money movement, or durable data.

## 1. Release Shape

Choose the narrowest rollout that proves the control:

| Shape | Use When |
|---|---|
| Shadow mode | Need to compare decisions without taking action |
| Dry run | Need planned actions and diffs before execution |
| Internal allowlist | Need human users to dogfood before broad release |
| Percentage rollout | Workflow is already observable and reversible |
| Full release | Evals, monitoring, rollback, and ownership are proven |

## 2. Required Gates

Every rollout plan needs:

- owner and on-call path
- user/account population
- start and stop criteria
- approval requirements for high-impact tools
- eval suite and minimum passing threshold
- telemetry dashboard or query
- rollback command or disable switch
- post-rollout review time

## 3. Monitoring

Track:

- tool call success/failure rates
- denied and approved high-impact actions
- user-visible errors or intervention rate
- stale memory or missing-context incidents
- rollback/abort activations
- cost, quota, or rate-limit burn

Avoid logging secrets, raw PII, or complete external documents unless the
system explicitly requires that evidence and has retention controls.

## 4. Rollback And Containment

Rollback must be easier than rollout. Prefer:

- feature flags for agent autonomy level
- kill switches for write-capable tools
- denylist updates for specific commands or integrations
- reverting prompts/policies separately from code when possible
- quarantining memory or state written during the rollout

Define who can trigger rollback and what evidence they need after rollback.
